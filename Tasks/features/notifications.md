# Technical Specification: Notification System

This document outlines the architecture and requirements for the HyPot-News notification system, enabling timely updates via Email and Mobile Push.

## 1. Notification Channels

### 1.1 Mobile Push Notifications
- **Provider**: Firebase Cloud Messaging (FCM).
- **Triggers**: Breaking news, completion of a sync cycle, or personalized alerts.
- **Client Handling**: Flutter app registers the FCM token and listens for data payloads even when the app is in the background.

### 1.2 Email Notifications
- **Provider**: AWS SES or SendGrid.
- **Content**: HTML-formatted emails showcasing the morning briefing headlines and a direct link to the app.

---

## 2. Notification Events & Triggers

| Event                    | Channel      | Trigger Condition                                                      |
| :----------------------- | :----------- | :--------------------------------------------------------------------- |
| **Daily Briefing Ready** | Push & Email | Once the `news/sync` finishes processing for a user's preferred genre. |
| **Breaking News**        | Push         | Triggered manually or by real-time filters for critical events.        |
| **Subscription Renewal** | Email        | 3 days before expiry and immediately upon renewal.                     |

---

## 3. Technical Architecture

### 3.1 Background Workers
- **Queue**: RabbitMQ/Redis.
- **Worker**: Celery (Python).
- **Workflow**:
    1. A sync task completes.
    2. A `send_notification_task` is dispatched to the worker.
    3. The worker fetches user preferences (`email_notifications_enabled`, `push_notifications_enabled`).
    4. If enabled, the worker constructs the payload and calls the respective provider API (FCM/SES).

### 3.2 Payload Structure (Push)
```json
{
  "to": "/topics/finance",
  "notification": {
    "title": "Your Morning Briefing is Ready",
    "body": "Top 10 stories in Finance are processed and ready for playback."
  },
  "data": {
    "article_id": "...",
    "action": "open_briefing"
  }
}
```

---

## 4. User Control (Opt-out)
Users can toggle these settings in the **Settings** screen. 
- Disabling a channel immediately updates the `users` table.
- Workers MUST check these parity bits before dispatching any notification.
