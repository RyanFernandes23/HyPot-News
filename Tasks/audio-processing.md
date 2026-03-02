# Technical Specification: Audio Processing & HLS Streaming

This document details the audio generation, transcoding, and streaming architecture for HyPot-News, ensuring a low-latency, high-quality "Morning Briefing" experience.

## 1. The Qwen-3 Processing Pipeline

The `POST /api/v1/news/sync` endpoint initiates a multi-stage background pipeline for each new article:

### A. Intelligence Stage (LLM)
- **Summarization**: The **LLM** processes the raw article content to generate:
    - **Briefing Headline**: A punchy, 1-sentence highlight.
    - **Detailed Summary**: A 3-5 sentence narrative for the "Deep Dive" view.

### B. Generation Stage (TTS)
- **TTS Synthesis**: The generated text is sent to the **Qwen-3 TTS** engine.
- **Output**: Returns high-bitrate PCM or MP3 data for both the headline and the summary.

### C. Transcoding Stage (FFmpeg)
- **HLS Packaging**: The raw audio is processed via **FFmpeg** using the following parameters:
    - **Segments**: Broken into `.ts` chunks (target duration: 6 seconds).
    - **Playlist**: Generates an `.m3u8` index file.
- **Why HLS?**: Allows the frontend to start playback immediately after the first 6-second chunk is buffered, rather than waiting for the entire file.

---

## 2. Storage & Database Integration

### Cloud Storage (AWS S3 / MinIO)
Final assets are stored in a hierarchical structure to support multiple voice profiles and high-quality playback speeds:
- `audio/{article_id}/{type}/{voice_profile}/{speed}/index.m3u8` (+ segments)

**Example Hierarchy**:
- `audio/123/headline/male_anchor/1.0/index.m3u8`
- `audio/123/headline/male_anchor/1.5/index.m3u8`

**Speeds Supported**: `0.75`, `1.0`, `1.25`, `1.5`, `2.0`.

### C. Transcoding Stage (FFmpeg / TTS)
- **High-Quality Speed Adjustment**: To avoid the "choppy" effect of browser-based time-stretching, the **Qwen-3 TTS** or **FFmpeg (with `atempo` filter)** generates separate audio files for each supported speed during the sync phase.

### Database Mapping
We store the playlist entry points in the `news_articles` table. Refer to [db-schema.md](./db-schema.md) for full definitions.

```sql
-- Key fields for audio playback
headline_hls_url  -- CDN URL to the headline .m3u8
summary_hls_url   -- CDN URL to the summary .m3u8
duration_seconds  -- Used by the UI to calculate slide progress
```

---

## 3. Frontend Consumption

The client application (Next.js/Flutter) consumes these streams using an HLS-capable player.

### Playback Logic:
1. **Pre-fetching**: In the "Morning Briefing", the app pre-loads the `.m3u8` of the *next* story in the queue while the current one is playing.
2. **Synchronization**: The frontend uses the article's `duration_seconds` to drive the visual progress bar and trigger the `BriefingSlider` transition if `onEnd` events are delayed by network jitter.
3. **Deep Dive Transition**: When a user taps "Instant Dive", the player seamlessly switches from the `headline` playlist to the `summary` playlist.

---

## 4. Error Handling & Fallbacks
- **Processing Failover**: If Qwen-3 TTS fails, the system logs the error and marks the article as "No Audio" to prevent frontend playback crashes.
- **Stale Content**: Articles older than 24 hours have their audio segments cleaned up via S3 Lifecycle Policies to optimize storage costs.
