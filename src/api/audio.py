from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from src.services.storage.s3 import s3_service
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()
logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 256  # 256KB — good for .ts segments
_executor = ThreadPoolExecutor(max_workers=10)

CONTENT_TYPES = {
    "m3u8": "application/vnd.apple.mpegurl",
    "ts":   "video/mp2t",
}

@router.get("/audio/{article_id}/{audio_type}/{filename}")
async def proxy_audio_file(
    article_id: str,
    audio_type: str,
    filename: str,
    request: Request,
):
    object_name = f"articles/{article_id}/{audio_type}/{filename}"
    ext = filename.rsplit(".", 1)[-1].lower()
    content_type = CONTENT_TYPES.get(ext, "application/octet-stream")

    # Run blocking S3 call in thread pool so it doesn't block the event loop
    loop = asyncio.get_event_loop()
    try:
        s3_resp = await loop.run_in_executor(
            _executor,
            lambda: s3_service.get_file_stream(object_name)
        )
    except Exception as e:
        logger.error(f"S3 fetch failed for {object_name}: {e}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    content_length = s3_resp.get("ContentLength")
    etag = s3_resp.get("ETag", "").strip('"')

    # ETag-based 304 — player skips re-download if it already has this version
    if etag and request.headers.get("If-None-Match") == etag:
        return Response(status_code=304)

    headers = {
        "Cache-Control": "no-cache" if ext == "m3u8" else "max-age=3600",
        "Access-Control-Allow-Origin": "*",
        "Accept-Ranges": "bytes",
    }
    if content_length:
        headers["Content-Length"] = str(content_length)
    if etag:
        headers["ETag"] = etag

    body = s3_resp["Body"]

    async def _stream():
        try:
            # Run each blocking read in executor to stay non-blocking
            while True:
                chunk = await loop.run_in_executor(_executor, lambda: body.read(CHUNK_SIZE))
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            logger.error(f"Stream interrupted for {object_name}: {e}")
        finally:
            body.close()

    return StreamingResponse(
        _stream(),
        media_type=content_type,
        headers=headers,
    )