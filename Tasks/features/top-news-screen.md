# Implementation Plan: Top News Screen (Morning Briefing)

This document outlines the specific tasks and technical requirements for the "Morning Briefing" screen, serving as a roadmap for both frontend and backend development.

## 1. Backend Architecture (FastAPI)

The backend is responsible for aggregating news, processing it through the Qwen-3 pipeline, and serving the HLS-compatible data to the client.

### Core Responsibilities:
- **Sync Engine**: `POST /api/v1/news/sync` - Fetches from NewsAPI, generates summaries/headlines via Qwen-3, and transcodes audio to HLS segments using FFmpeg.
- **Data Serving**: `GET /api/v1/news/briefing` - Returns a standardized list of articles for the selected genre and volume (10, 20, 30). **Note**: To ensure consistency and high performance, all users selecting the same category and volume will receive the same set of top news for that day/sync cycle.
- **HLS Management**: Manages and serves the `.m3u8` playlists and `.ts` audio segments stored in S3/MinIO.

### Database Reference:
See [db-schema.md](../architecture/db-schema.md) for table definitions (`news_articles`, `users`, `bookmarks`).

---

## 2. Frontend Implementation (Next.js / Flutter)

The "Top News" screen provides a high-quality, hands-free slideshow experience.

### Key Components:
- **`BriefingSlider`**: A full-screen carousel module.
- **`HLSPlayer`**: The core audio engine. It works in tandem with the **[PlaybackHUD](../features/audio-player-ui.md)** to provide play/pause, seek, and speed controls.
- **`PlaybackHUD`**: User interface overlay with dynamic progress bars.

### UX Logic:
1. **Pre-fetch**: The application fetches the briefing data and constructs the final HLS URLs:
   `url = article.headline_hls_base_url + "/" + voice + "/" + speed + "/index.m3u8"`
2. **Auto-Transition**: Automatically advances to the next story once `onEnd` is triggered.
3. **Session State**: Remembers which articles were played during the current session to avoid repetition on a quick re-open.

---

## 3. Configuration & Personalization

Before the briefing starts, the user can configure:
- **Genres**: International, Finance, Regional, Good News, Hot Topics.
- **Volume**: 10, 20, or 30 stories.
- **Themes**: Standard or HD Images mode.