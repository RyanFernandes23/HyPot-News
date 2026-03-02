# Technical Specification: Content & Playback Preferences

This document provides the detailed implementation roadmap for user-controlled content filtering and audio playback behavior.

## 1. Genre Selection & Interests Engine

### Backend Implementation:
- **Storage**: Store choices as a list of strings in the `interests` JSONB column of the `users` table.
- **Filtering Logic**:
    - When fetching top news, prioritize the user's selected genres using an `IN` clause or specialized GIN index query.
    - **Fallback**: If the user has no genres selected, return the "Hot Topics" or "International" default.

### Frontend Implementation:
- **Interactive Interest Picker**: A grid of toggleable "chips" with icons.
- **Immediate Feedback**: Changes should trigger a refresh of the current briefing queue if the user is on the Home screen.

---

## 2. Dynamic News Volume

### Technical Flow:
1.  **Selection**: User chooses 10, 20, or 30 articles in Settings.
2.  **Persistence**: The value is updated in the `users` table via `PATCH /api/v1/user/preferences`.
3.  **Consumption**: The frontend includes this value in the `limit` query parameter for all news requests:
    `GET /api/v1/news/briefing?limit=20`

---

## 3. Advanced Autoplay & Transition Engine

The goal is to provide a "hands-free" radio-like experience.

### Playback Logic:
- **Detailed Summary Autoplay**: A boolean flag in the app's global state (`is_summary_autoplay_enabled`). If true, the `HLSPlayer` in the Deep Dive screen triggers `play()` on mount.
- **Genre Transition Countdown**: 
    - Triggered when `Scenario B` (end of queue) is reached.
    - **Countdown Component**: A 10-second visual timer overlay.
    - **Pre-fetching**: While the timer counts down, the app background-fetches the `m3u8` for the first story of the *next* preferred genre.

---

## 4. Audio Tuning & TTS Personalization

### Playback Speed:
- **Implementation**: To ensure high-quality audio, the app fetches a specific HLS playlist pre-generated for the desired speed.
- **Logic**: 
    `speed_val = user_pref.playback_speed || "1.0"`
    `final_url = base_url + "/" + voice + "/" + speed_val + "/index.m3u8"`
- **Range**: 0.75x, 1.0x, 1.25x, 1.5x, 2.0x.

### Voice & Language:
- **Voice Profiles**: The backend `sync` process generates audio for multiple "profiles" (e.g., *Male Anchor*, *Female Assistant*) where available.
- **Selection**: The user chooses a profile in Settings, and the frontend appends the appropriate suffix to the audio URLs:
    `audio_url = article.hls_url_base + "/" + user_pref.voice_profile + ".m3u8"`

---

## 5. Mobile Background Playback (Flutter)
- **Audio Service**: Use `just_audio_background` or similar to handle playback while the app is in the background or the screen is locked.
- **Lock Screen Controls**: Display article title, source, and provide Skip/Pause functionality.
