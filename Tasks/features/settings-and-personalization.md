# Technical Specification: Settings & Personalization

The Settings page is the central hub for tailoring the user experience, managing authentication, and handling subscriptions.

## 1. Profile & Authentication
- **Authentication**: Sign In/Sign Up pages with JWT-based sessions.
- **Profile Management**: Update username, email, and password.
- **Personalized Bookmarks**: A dedicated view to manage and revisit saved articles. (See [db-schema.md](../architecture/db-schema.md#bookmarks)).

---

## 2. Content & Playback Preferences
These settings directly influence how news is filtered and played back across the app.

For a deep dive into the technical implementation of genres, volume, autoplay, and audio tuning, see:
**[Content & Playback Preferences Detailed Plan](../features/content-playback-preferences.md)**

---

## 3. Notifications & Alerts
Stay updated with the latest news even when you're not using the app.

- **Email Notifications**: Toggle to receive a daily digest of your morning briefing.
- **Mobile Push Notifications**: Real-time alerts for breaking news and when your briefing is ready.
- **Notification Opt-out**: Simple global toggle to turn off all alerts.

For technical details on FCM and Email integration, see:
**[Notification System Detailed Plan](../features/notifications.md)**

---

## 4. Visuals & Themes
- **Theme Mode**: System default, Light Mode, or Dark Mode toggle.
- **Image Quality**: 
    - **Standard**: Optimized for speed/data saving.
    - **HD Images**: High-resolution assets for a premium feel.
- **Accessibility**: Adjustable text scaling (Small, Medium, Large).

---

## 5. Subscription & Premium
Manage your plan status and access premium features.

For a detailed implementation plan covering RevenueCat integration and feature unlocking (HD images, unlimited bookmarks, etc.), see:
**[Subscription & Premium Detailed Plan](../features/subscription-premium.md)**

---

## 6. Technical Implementation (Frontend/Backend)

### Backend Requirements:
- **`PATCH /api/v1/user/preferences`**: Updates the `interests`, `preferred_volume`, and `theme` fields in the `users` table.
- **`GET /api/v1/user/bookmarks`**: Fetches paginated bookmarked articles.

### Frontend Requirements:
- **Global Theme Provider**: Next.js theme-switching logic.
- **Settings State**: Persistent local storage/state for immediate UI feedback on preference changes.
