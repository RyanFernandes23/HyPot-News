# User API Documentation

Endpoints for managing user profiles, preferences, and bookmarks.

## Update User Preferences
### `PATCH /api/v1/user/preferences`

Updates the user's news interests, playback volume, and other personal settings.

**Request Body (JSON):**
```json
{
  "interests": ["International", "Finance"],
  "briefing_volume": 20,
  "playback_speed": "1.25",
  "voice_profile": "female_assistant",
  "email_notifications_enabled": true,
  "push_notifications_enabled": true,
  "fcm_token": "fcm_token_string"
}
```

**Response Body (JSON):**
```json
{
  "status": "updated",
  "preferences": { ... }
}
```

---

## Create Bookmark
### `POST /api/v1/user/bookmarks`

Saves an article to the user's bookmarks list.

**Request Body (JSON):**
```json
{
  "article_id": "uuid"
}
```

**Response Body (JSON):**
```json
{
  "status": "bookmarked",
  "bookmark_id": "uuid"
}
```

**Validation:**
- Free tier: Limited to 10 bookmarks. Returns `402 Payment Required` if limit is reached.
- Pro tier: Unlimited bookmarks.

---

## Get Bookmarks
### `GET /api/v1/user/bookmarks`

Retrieves the list of articles bookmarked by the user.

**Response Body (JSON):**
```json
[
  {
    "id": "uuid",
    "article_id": "uuid",
    "title": "...",
    "url_to_image": "...",
    "created_at": "timestamp"
  },
  ...
]
```
