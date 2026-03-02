# Database Schema Design

This document outlines the database structure for HyPot-News, supporting multi-platform news delivery, HLS audio streaming, and user personalization.

## 1. Primary Tables

### `users`
Stores user profile information and preferences.
- `id`: `UUID` (Primary Key, Default: `uuid_generate_v4()`)
- `username`: `VARCHAR(50)` (Unique, Not Null)
- `email`: `VARCHAR(255)` (Unique, Not Null)
- `password_hash`: `TEXT` (Not Null)
- `interests`: `JSONB` (Default: `[]`, List of categories like 'Finance', 'International')
- `preferred_volume`: `INTEGER` (Default: `10`, choices: 10, 20, 30)
- **Notification Preferences**:
    - `email_notifications_enabled`: `BOOLEAN` (Default: `TRUE`)
    - `push_notifications_enabled`: `BOOLEAN` (Default: `TRUE`)
    - `fcm_token`: `VARCHAR(255)` (Link to mobile device for push)
- `created_at`: `TIMESTAMP WITH TIME ZONE` (Default: `NOW()`)
- `updated_at`: `TIMESTAMP WITH TIME ZONE` (Default: `NOW()`)

### `news_articles`
Stores processed news content and HLS asset references.
- `id`: `UUID` (Primary Key)
- `external_id`: `VARCHAR(255)` (Unique, hash of source URL/Title to prevent duplicates)
- `source_name`: `VARCHAR(100)`
- `author`: `VARCHAR(255)`
- `title`: `TEXT` (Not Null)
- `description`: `TEXT`
- `content`: `TEXT` (Full article body)
- `summarized_content`: `TEXT` (3-5 sentence deep dive summary)
- `url`: `TEXT` (Original source link)
- `url_to_image`: `TEXT`
- `category`: `VARCHAR(50)` (Indexed)
- `published_at`: `TIMESTAMP WITH TIME ZONE`
- **HLS Assets**:
    - `headline_hls_base_url`: `TEXT` (Base URL to headline HLS folder)
    - `summary_hls_base_url`: `TEXT` (Base URL to summary HLS folder)
    - `available_voices`: `JSONB` (e.g., `["male_anchor", "female_assistant"]`)
    - `available_speeds`: `JSONB` (e.g., `["0.75", "1.0", "1.5"]`)
    - `duration_seconds`: `INTEGER` (Total audio length for briefing sync)
- `raw_data`: `JSONB` (Original NewsAPI response for audit/NoSQL migration)
- `created_at`: `TIMESTAMP WITH TIME ZONE` (Default: `NOW()`)

### `bookmarks`
Links users to their saved articles.
- `user_id`: `UUID` (Foreign Key -> `users.id`)
- `article_id`: `UUID` (Foreign Key -> `news_articles.id`)
- `created_at`: `TIMESTAMP WITH TIME ZONE` (Default: `NOW()`)
- *Primary Key*: `(user_id, article_id)`

## 2. Design Choices

### Why PostgreSQL with JSONB?
- **Relational Integrity**: Essential for managing users, bookmarks, and subscriptions.
- **Flexibility**: The `raw_data` and `interests` fields use `JSONB`, allowing us to store semi-structured data without the overhead of complex many-to-many tables.
- **Search**: PostgreSQL's GIN indexes on `JSONB` and Full-Text Search capabilities are ideal for news discovery.

### HLS Integration
Instead of storing binary audio, we store URLs to **S3-hosted HLS playlists**. This offloads the heavy lifting of audio delivery to a CDN/Object Storage, keeping the database slim and performant.

### Deduplication
The `external_id` field is critical. Since NewsAPI can return the same story from different sources or during different sync cycles, we generate a unique hash to ensure each story is only processed and stored once.
