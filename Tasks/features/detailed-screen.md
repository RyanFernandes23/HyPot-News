# Technical Specification: Detailed News Screen (Deep Dive)

The "Detailed News Screen" is designed for in-depth engagement with specific stories, transitioning from a brief headline to full article content, detailed audio summaries, and video integration.

## 1. Backend Integration (FastAPI)

The backend must serve the enriched content required for the deep-dive experience.

### API Endpoint: `GET /api/v1/news/{article_id}`
- **Response Shape**:
    - `full_content`: The complete article body.
    - `summary_hls_base_url`: Base link to the HLS summary audio folder.
    - `available_voices`: `["male_anchor", "female_assistant", ...]`
    - `available_speeds`: `["0.75", "1.0", "1.25", "1.5", "2.0"]`
    - `video_url`: Embedded source for video news.
    - `source_attribution`: Author and publisher metadata.
    - `related_articles`: A list of 5 articles for post-read navigation.

---

## 2. Frontend Implementation (Next.js / Flutter)

- **`ContinuousAudioPlayer`**: Integrated player HUD for deep-dive summaries. See **[Audio Player UI](../features/audio-player-ui.md)** for detailed control specifications (Rewind, Forward, Speed).
- **`ContentRenderer`**: Reader view with progress indicators.
- **`NavigationDock`**: Floating controls with "Next in Queue".

### 1.1 `related_articles` Logic

**Fetching (Category + Time + Title Similarity)**: 
*   The backend filters by **Category** (1), limits by **Time** (3 - e.g., last 48 hours), and then applies **Title Similarity** (2).
*   Finally, it **Sorts** by relevance and recency (4).
    ```sql
    SELECT id, title, url_to_image, category 
    FROM news_articles 
    WHERE category = :current_category              -- 1. Category
      AND published_at >= NOW() - INTERVAL '48 hours' -- 3. Time
      AND title_search_vector @@ websearch_to_tsquery(:current_title) -- 2. Title
      AND id != :current_id 
    ORDER BY ts_rank(title_search_vector, websearch_to_tsquery(:current_title)) DESC, 
             published_at DESC LIMIT 5;             -- 4. Sort
    ```

### 1.2 "Related News Slideshow" Mode
When the user selects **"Read Related News"** from the Transition Overlay:
- The app enters a **Temporary Queue** of the fetched related articles.
- **Continuous Playback**: It plays the **Detailed Summary** (`summary_hls_url`) of each article one after another.
- **Experience**: The user can swipe through these detailed views as a slideshow, focusing on the deeper content of related topics.

---

## 3. Post-Deep Dive Playback & Transitions

Once the detailed summary audio finishes, the application follows this automated logic:

### 3.1 Scenario A: More articles in current briefing
- **Action**: The UI pops back to the [Top News Screen](../features/top-news-screen.md) or remains in a "minimal reader" mode.
- **Playback**: Continues reading the **headline** of the next article in the current queue automatically.

### 3.2 Scenario B: Last article in current briefing
- **Action**: A **Transition Overlay** appears with a 5-10 second countdown timer.
- **Next Queue**: The backend/frontend prepares a new "Top News" set from a *different* genre based on user preferences.
- **UI Elements**:
    - **Timer**: "Starting next briefing (Finance) in 5s..."
    - **Read Related News (Optional)**: A button to ignore the auto-transition and explore the `related_articles` manually.
- **Completion**: Once the timer hits zero, the app starts playing the first headline of the new genre.

---

## 4. Component Updates

- **`NavigationDock`**: 
    - Floating controls with "Next in Queue".
    - "Bookmark" and "Share" buttons.
- **`TransitionTimer`**: 
    - Circular progress indicator for the end-of-queue countdown.
    - Layout: `[ Cancel/Read Related ]  [ Timer ]  [ Start Now ]`.

---

## 5. State Management

- **Queue Memory**: The frontend must maintain the "Briefing Queue" in its global state (e.g., Redux/Zustand) to support the "Next in Queue" functionality across different screens.
- **Reading History**: Tracks whether an article was "Deep Dived" to update the user's personalization profile in the database.
