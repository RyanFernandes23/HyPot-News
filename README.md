# HyPot-News

A text-to-speech application designed to deliver daily news seamlessly across web and mobile platforms.

## Project Structure

This application is built with a separated architecture, utilizing distinct directories for the client and server:
- `/frontend`: Contains the user interface and client-side logic.
- `/backend`: Houses the API, data models, and backend services.

## Overview

HyPot-News aims to provide users with an engaging daily digest of top headlines and detailed news stories, delivered via text, imagery, and audio (Text-to-Speech).

### User Experience

1. **Morning Briefing:** Users open the application to discover the top 10, 20, or 30 news stories of the day.
2. **Audio Playback & Slideshow:** Pressing the play button reads the headlines aloud sequentially, accompanied by a dynamic slideshow featuring the corresponding text and images.
3. **Deep Dive:** If a particular story captures the user's interest, they can navigate to a detailed news screen. The application will then begin playing the full, detailed audio for that specific article.
4. **Seamless Navigation:** After finishing a detailed story, users can easily return to the top news briefing or skip ahead to the next detailed article.

## Detailed Product Specifications

### 1. Top News Screen (Daily Briefing)
The "Top News" screen provides a hands-free, automated experience for catching up on the day's highlights.
- **Initial Configuration**: Before starting, users select:
    - **Genre/Interest**: International, Finance, Regional, Good News, or Hot Topics.
    - **News Volume**: Choice of top 10, 20, or 30 stories.
- **Interactive Slideshow**: Full-screen images with headline overlays.
- **Dynamic Playback**: Headlines are read via TTS, and slides transition automatically based on audio duration.
- **Controls**: Users can pause/resume, skip stories, bookmark highlights for later, or share directly from the briefing.
- **Instant Dive**: A single tap on any story during the briefing navigates to its detailed view.

### 2. Detailed News Screen (Deep Dive)
Designed for in-depth engagement with specific stories.
- **Full Content**: Displays full article text, source attribution, and high-resolution media.
- **Continuous Audio**: Plays the full-length TTS version of the article.
- **Video Integration**: Embedded webview for video news with a visual playback timeline/progress bar.
- **Sequential Playback**: Logic usually follows a brief audio summary followed by video autoplay.
- **Social & Utility**: Dedicated Bookmark and Share buttons.
- **Queue Flow**: "Next in Queue" button to proceed to the next story in the briefing sequence without returning to the main menu.

### 3. Settings & Personalization
A comprehensive center for tailoring the user experience:
- **Profile & Auth**: Dedicated Sign In/Sign Up pages, Profile management, and historical Bookmarks.
- **Subscription**: Management of Subscription Plans and a "Subscribe to Premium" call-to-action.
- **Visuals & Themes**: Dark Mode/Light Mode toggle and choice between Standard or **HD Images**.
- **Accessibility**: Adjustable text size, primary Language selection, and Audio (TTS) language selection.
- **Playback Tuning**: Toggle for **Autoplay during detailed news** and general notification management for alerts.

## Technology Stack

Our chosen technology stack is designed for scalability, cross-platform compatibility, and an optimized, media-rich experience:

| Component                | Primary Technology      | Alternatives / Tradeoffs                                                            |
| :----------------------- | :---------------------- | :---------------------------------------------------------------------------------- |
| **Web Frontend**         | Next.js                 |                                                                                     |
| **Mobile Frontend**      | Flutter                 | Expo (Pending research)                                                             |
| **Backend API**          | Python (FastAPI)        |                                                                                     |
| **Database**             | PostgreSQL (Relational) | MongoDB (NoSQL) - Chosen for flexibility with NewsAPI data if scaling horizontally. |
| **News Data Source**     | NewsAPI                 | Custom Web Scraping                                                                 |
| **Asset Storage**        | AWS S3                  | MinIO (Local development)                                                           |
| **Text-to-Speech (TTS)** | Qwen-3 (Hosted)         | Scalable, high-quality local/hosted model.                                          |


-------------------------------------------------------------------
worker -> uv run -m src.worker

tts -> uv run modal deploy qwen-3-tts-modal.py

fastapi -> uvicorn src.main:app --reload