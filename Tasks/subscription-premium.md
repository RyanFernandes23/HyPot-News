# Technical Specification: Subscription & Premium

This document details the implementation of the HyPot-News premium tier, leveraging **RevenueCat** or **Stripe** to manage entitlements and unlock advanced features.

## 1. Subscription Logic & Entitlements

We define two primary tiers: **Free** and **Pro**.

### Premium (Pro) Features:
- **HD Images**: Access to high-resolution news imagery for the briefing.
- **Ad-free Experience**: Removal of interstitial or banner advertisements.
- **High-Quality Voices**: Access to the most advanced Qwen-3 TTS voice profiles.
- **Unlimited Bookmarks**: No cap on the number of saved articles.

---

## 2. Technical Integration (RevenueCat)

We recommend **RevenueCat** for cross-platform entitlement management.

### Backend Requirements:
- **Webhook Listener**: `POST /api/v1/webhooks/revenuecat`
    - Listens for `INITIAL_PURCHASE`, `RENEWAL`, and `CANCELLATION` events.
    - Updates the `subscription_status` in our PostgreSQL `users` table.
- **Entitlement Checks**: A middleware or dependency that checks the user's current status before returning premium assets (e.g., HD image URLs or Pro voice HLS playlists).

### Frontend Requirements:
- **Paywall Hook**: Use RevenueCat's SDK to fetch current offerings and display a premium paywall.
- **Entitlement State**: The app globally listens for entitlement changes to update the UI (e.g., removing ads, enabling HD toggle).

---

## 3. Database Schema Updates

Refer to [db-schema.md](./db-schema.md) for details.

### `users` table additions:
- `subscription_tier`: `VARCHAR(20)` (Default: 'free', values: 'free', 'pro')
- `subscription_expires_at`: `TIMESTAMP WITH TIME ZONE`
- `revenuecat_id`: `VARCHAR(255)` (Link to the external billing profile)

---

## 4. Feature Unlocking Flow

### HD Images & High-Quality Voices:
When the frontend calls `GET /api/v1/news/briefing`:
1. The backend verifies the user's `subscription_tier`.
2. **If Pro**: Returns `url_to_hd_image` and adds high-quality options to `available_voices`.
3. **If Free**: Returns standard `url_to_image` and only basic voice profiles.

### Unlimited Bookmarks:
1. `POST /api/v1/user/bookmarks` checks the count of existing bookmarks for the user.
2. If `count >= 10` (or another limit) and user is **Free**, the request is rejected with a `402 Payment Required` error.

---

## 5. Security & Verification
- **Server-to-Server Verification**: We rely on RevenueCat/Stripe webhooks for the source of truth, rather than letting the client-side dictate its own status.
- **Grace Periods**: Handle subscription expiration gracefully by allowing a 24-48 hour window before stripping "Pro" access.
