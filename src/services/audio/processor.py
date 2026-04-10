import io
import os
import uuid
import logging
import subprocess
import modal
import shutil
import asyncio
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from src.core.config import settings
from src.db.supabase import supabase_service
from src.services.storage.s3 import s3_service

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self):
        self.temp_dir = settings.TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)

        # Initialize static-ffmpeg
        import static_ffmpeg

        static_ffmpeg.add_paths()
        self.ffmpeg_path = "ffmpeg"

        # Thread pool for concurrent local processing (FFmpeg + S3)
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def process_daily_briefing_article(self, article: Dict[str, Any]):
        """
        Processes a daily briefing article from daily_briefing_articles table.
        Uses headline + description fields.
        """
        article_id = article["id"]
        logger.info(f"Processing daily briefing audio for article {article_id}")

        supabase_service.table("daily_briefing_articles").update(
            {"audio_status": "processing"}
        ).eq("id", article_id).execute()

        tasks = [
            {
                "id": article_id,
                "text": article["headline"],
                "lang": "English",
                "type": "headline",
            },
            {
                "id": article_id,
                "text": article["description"],
                "lang": "English",
                "type": "summary",
            },
        ]

        try:
            processor_cls = modal.Cls.from_name("qwen3-news-batch", "NewsProcessor")
            processor_instance = processor_cls()

            audios = {}
            task_idx = 0
            async for result in processor_instance.synthesize.map.aio(tasks):
                audio_type = tasks[task_idx]["type"]
                audios[audio_type] = result["audio"]
                task_idx += 1

            if "headline" in audios and "summary" in audios:
                self._finalize_daily_briefing(article_id, audios)
                logger.info(
                    f"Successfully processed daily briefing article {article_id}"
                )

        except Exception as e:
            logger.error(
                f"Daily briefing audio processing failed for {article_id}: {e}"
            )
            new_attempts = article.get("audio_attempts", 0) + 1
            status = f"failed({new_attempts})"
            supabase_service.table("daily_briefing_articles").update(
                {"audio_status": status, "audio_attempts": new_attempts}
            ).eq("id", article_id).execute()
            raise e

    def _finalize_daily_briefing(self, article_id: str, audios: Dict[str, bytes]):
        """Finalize daily briefing article audio."""
        import uuid

        hls_urls = {}

        for audio_type, audio_data in audios.items():
            if not audio_data:
                continue

            work_dir = os.path.join(self.temp_dir, str(uuid.uuid4()))
            os.makedirs(work_dir, exist_ok=True)

            try:
                text = (
                    audio_data.decode("utf-8")
                    if isinstance(audio_data, bytes)
                    else audio_data
                )

                playlist_filename = f"{audio_type}.m3u8"
                playlist_path = os.path.join(work_dir, playlist_filename)

                with open(playlist_path, "w", encoding="utf-8") as f:
                    f.write(text)

                s3_base_path = f"daily_briefing/{article_id}/{audio_type}"
                object_name = f"{s3_base_path}/{playlist_filename}"
                url = s3_service.upload_file(
                    playlist_path, object_name, "application/vnd.apple.mpegurl"
                )
                hls_urls[audio_type] = url

            finally:
                if os.path.exists(work_dir):
                    shutil.rmtree(work_dir, ignore_errors=True)

        supabase_service.table("daily_briefing_articles").update(
            {
                "headline_hls_url": hls_urls.get("headline"),
                "summary_hls_url": hls_urls.get("summary"),
                "audio_status": "ready",
            }
        ).eq("id", article_id).execute()

    async def process_single_article(self, article: Dict[str, Any]):
        """
        Processes a single article through the synthesis and finalization flow.
        """
        article_id = article["id"]
        logger.info(f"Processing single audio task for article {article_id}")

        # Update to processing
        supabase_service.table("news_articles").update(
            {"audio_status": "processing"}
        ).eq("id", article_id).execute()

        tasks = [
            {
                "id": article_id,
                "text": article["headline"],
                "lang": "English",
                "type": "headline",
            },
            {
                "id": article_id,
                "text": article["summarized_content"],
                "lang": "English",
                "type": "summary",
            },
        ]

        try:
            processor_cls = modal.Cls.from_name("qwen3-news-batch", "NewsProcessor")
            processor_instance = processor_cls()

            audios = {}
            task_idx = 0
            async for result in processor_instance.synthesize.map.aio(tasks):
                audio_type = tasks[task_idx]["type"]
                audios[audio_type] = result["audio"]
                task_idx += 1

            if "headline" in audios and "summary" in audios:
                # Finalize synchronously here so the task is truly finished
                self._finalize_article(
                    article_id, audios, article.get("audio_attempts", 0)
                )
                logger.info(f"Successfully processed single article {article_id}")

        except Exception as e:
            logger.error(
                f"Single article audio processing failed for {article_id}: {e}"
            )
            new_attempts = article.get("audio_attempts", 0) + 1
            status = f"failed({new_attempts})"
            supabase_service.table("news_articles").update(
                {"audio_status": status, "audio_attempts": new_attempts}
            ).eq("id", article_id).execute()
            raise e

    async def process_batch(self, articles: List[Dict[str, Any]]):
        """
        Processes a batch of articles in parallel using Modal map.
        """
        if not articles:
            return

        article_ids = [a["id"] for a in articles]
        logger.info(f"Batch processing audio for {len(article_ids)} articles.")

        # Update all to processing
        supabase_service.table("news_articles").update(
            {"audio_status": "processing"}
        ).in_("id", article_ids).execute()

        # Prepare inputs for Modal
        # We need to process both headline and summary for each article.
        # To maintain parallel efficiency, we'll flatten these into a single list of tasks.
        tasks = []
        for article in articles:
            tasks.append(
                {
                    "id": article["id"],  # Matches NewsProcessor.synthesize expectation
                    "text": article["headline"],
                    "lang": "English",  # Default or detect
                    "type": "headline",
                }
            )
            tasks.append(
                {
                    "id": article["id"],
                    "text": article["summarized_content"],
                    "lang": "English",
                    "type": "summary",
                }
            )

        try:
            logger.info("Connecting to Modal app 'qwen3-news-batch'...")
            processor_cls = modal.Cls.from_name("qwen3-news-batch", "NewsProcessor")
            # Instantiate the class (creates a remote instance)
            processor_instance = processor_cls()

            logger.info(f"Starting Modal map for {len(tasks)} tasks...")

            # Track received parts for each article
            # {article_id: {"headline": bytes, "summary": bytes}}
            article_audios = {}
            # Keep track of submitted articles to avoid double submission
            submitted_articles = set()
            # Create a lookup for current attempts
            attempts_lookup = {a["id"]: a.get("audio_attempts", 0) for a in articles}

            # Map returns results in the same order as inputs.
            # We iterate as they come off the wire.
            task_idx = 0
            async for result in processor_instance.synthesize.map.aio(tasks):
                task_info = tasks[task_idx]
                article_id = task_info["id"]
                audio_type = task_info["type"]

                logger.info(
                    f"Received result for task {task_idx} ({audio_type}) for article {article_id}"
                )

                if article_id not in article_audios:
                    article_audios[article_id] = {}

                article_audios[article_id][audio_type] = result["audio"]
                task_idx += 1

                # Check if this article is now complete
                if (
                    "headline" in article_audios[article_id]
                    and "summary" in article_audios[article_id]
                ):
                    if article_id not in submitted_articles:
                        logger.info(
                            f"Article {article_id} is complete. Submitting for finalization."
                        )
                        current_attempts = attempts_lookup.get(article_id, 0)
                        self.executor.submit(
                            self._finalize_article,
                            article_id,
                            article_audios[article_id],
                            current_attempts,
                        )
                        submitted_articles.add(article_id)

            logger.info("All Modal tasks completed and streamed.")

        except Exception as e:
            logger.error(f"Batch audio processing encountered an error: {e}")
            # Mark remaining as failed with incremented attempts
            for article in articles:
                article_id = article["id"]
                if (
                    "submitted_articles" not in locals()
                    or article_id not in submitted_articles
                ):
                    new_attempts = article.get("audio_attempts", 0) + 1
                    status = f"failed({new_attempts})"
                    logger.warning(
                        f"Marking article {article_id} as failed due to batch error."
                    )

                    supabase_service.table("news_articles").update(
                        {"audio_status": status, "audio_attempts": new_attempts}
                    ).eq("id", article_id).execute()

    def _finalize_article(
        self, article_id: str, audios: Dict[str, bytes], current_attempts: int
    ):
        """
        Finalizes a single article's audio: chunks and uploads both headline and summary.
        """
        try:
            # Get the object key instead of the full URL
            headline_path = f"articles/{article_id}/headline/headline.m3u8"
            summary_path = f"articles/{article_id}/summary/summary.m3u8"

            self._chunk_and_upload(article_id, audios["headline"], "headline")
            self._chunk_and_upload(article_id, audios["summary"], "summary")

            supabase_service.table("news_articles").update(
                {
                    "headline_hls_base_url": headline_path,
                    "summary_hls_base_url": summary_path,
                    "audio_status": "ready",
                    "audio_attempts": 0,  # Reset on success
                }
            ).eq("id", article_id).execute()

            logger.info(f"Finalized article {article_id}")
        except Exception as e:
            logger.error(f"Failed to finalize article {article_id}: {e}")
            new_attempts = current_attempts + 1
            status = f"failed({new_attempts})"

            supabase_service.table("news_articles").update(
                {"audio_status": status, "audio_attempts": new_attempts}
            ).eq("id", article_id).execute()

    def _chunk_and_upload(
        self, article_id: str, audio_bytes: bytes, audio_type: str
    ) -> str:
        """
        Chunks WAV bytes, uploads to S3, and immediately cleans up tmp files.
        """
        run_id = str(uuid.uuid4())
        work_dir = os.path.join(self.temp_dir, run_id)
        os.makedirs(work_dir, exist_ok=True)

        try:
            wav_path = os.path.join(work_dir, "input.wav")
            with open(wav_path, "wb") as f:
                f.write(audio_bytes)

            playlist_filename = f"{audio_type}.m3u8"
            playlist_path = os.path.join(work_dir, playlist_filename)
            segment_pattern = os.path.join(work_dir, f"{audio_type}_chunk_%03d.ts")

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                wav_path,
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-f",
                "hls",
                "-hls_time",
                "6",
                "-hls_playlist_type",
                "vod",
                "-hls_segment_filename",
                segment_pattern,
                playlist_path,
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            # Upload to S3
            s3_base_path = f"articles/{article_id}/{audio_type}"
            hls_url = ""

            for root, _, files in os.walk(work_dir):
                for file in files:
                    if file.endswith((".ts", ".m3u8")):
                        file_path = os.path.join(root, file)
                        object_name = f"{s3_base_path}/{file}"
                        content_type = (
                            "application/vnd.apple.mpegurl"
                            if file.endswith(".m3u8")
                            else "video/MP2T"
                        )
                        url = s3_service.upload_file(
                            file_path, object_name, content_type
                        )
                        if file == playlist_filename:
                            hls_url = url

            return hls_url
        finally:
            # Clean up tmp files immediately instead of waiting for cleanup job
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir, ignore_errors=True)


audio_processor = AudioProcessor()
