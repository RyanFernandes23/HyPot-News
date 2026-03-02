# Technical Specification: Audio Player UI & Controls

This document details the user interface and functional logic for the global audio player used in both the "Morning Briefing" and "Detailed News" screens.

## 1. Primary Playback Controls

The player provides a premium, intuitive HUD (Heads-Up Display) for managing audio playback.

| Control          | Icon / Label           | Action                                                       |
| :--------------- | :--------------------- | :----------------------------------------------------------- |
| **Play / Pause** | `play_arrow` / `pause` | Toggles the active HLS stream state.                         |
| **Rewind**       | `replay_15`            | Seeks backward 15 seconds in the current segment.            |
| **Fast Forward** | `forward_15`           | Seeks forward 15 seconds (limited by buffer).                |
| **Previous**     | `skip_previous`        | Navigates to the start of the previous article in the queue. |
| **Next**         | `skip_next`            | Navigates to the start of the next article in the queue.     |

---

## 2. Advanced Audio Features

These settings allow users to curate their listening experience without leaving the player view.

- **Playback Speed Selector**: 
    - Options: `0.75x`, `1.0x`, `1.25x`, `1.5x`, `2.0x`.
    - Logic: Switches to the corresponding HLS playlist folder (e.g., `/1.5/index.m3u8`).
- **Voice Profile Switcher**: 
    - Quick-toggle between available AI voices (e.g., "Male Anchor" to "Female Assistant").
- **Sleep Timer**:
    - Optional countdown to stop playback after 15, 30, or 60 minutes.

---

## 3. Visual Components

- **Dynamic Progress Bar**: 
    - Shows current timestamp vs. total `duration_seconds`.
    - Draggable "Scrubber" for precision seeking.
- **Waveform Visualization**:
    - A subtle, animated CSS waveform that reacts to active playback.
- **Article Context Mini-Card**:
    - Displays the current article's headline, source name, and a small thumbnail image.

---

## 4. State Management & Logic

### 4.1 Seeking Logic (FFmpeg/HLS)
Since we use HLS, seeking forward beyond the current buffered segments may trigger a brief loading state as the player fetches the new `.ts` chunks for that timestamp.

### 4.2 Queue Persistence
The global state (Zustand/Redux) maintains the current `briefing_queue`.
- **`current_index`**: Tracks the active article.
- **`onEnd` Event**: Automatically increments `current_index` and loads the next `headline_hls_url`.

### 4.3 Background Playback
(Mobile Only) Uses `just_audio_background` to ensure the controls are accessible via the system lock screen and notification shade.
