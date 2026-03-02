# News API Documentation

Endpoints for fetching, syncing, and deep-diving into news content.

## Sync News
### `POST /api/v1/news/sync`

Triggers the background engine to fetch news from NewsAPI, process summaries through Qwen-3, and transcode audio to HLS.

**Response Body (JSON):**
```json
{
  "status": "success",
  "task_id": "uuid"
}
```

---

## Get Briefing
### `GET /api/v1/news/briefing`

Returns a standardized list of articles for the selected genre and volume.

**Query Parameters:**
- `genre`: `string` (e.g., "International", "Finance")
- `volume`: `integer` (10, 20, or 30)

**Response Shape (JSON):**
```json
[
  {
    "id": "uuid",
    "title": "...",
    "url_to_image": "...",
    "url_to_hd_image": "...",
    "headline_hls_base_url": "...",
    "category": "..."
  },
  ...
]
```

---

## Get Detailed News
### `GET /api/v1/news/{article_id}`

Retrieves enriched content for a specific article.

**Response Shape (JSON):**
```json
{
  "id": "uuid",
  "title": "...",
  "full_content": "...",
  "summary_hls_base_url": "...",
  "available_voices": ["male_anchor", "female_assistant"],
  "available_speeds": ["0.75", "1.0", "1.25", "1.5", "2.0"],
  "video_url": "...",
  "source_attribution": {
    "author": "...",
    "publisher": "..."
  },
  "related_articles": [
    {
      "id": "uuid",
      "title": "...",
      "url_to_image": "...",
      "category": "..."
    }
  ]
}
```
