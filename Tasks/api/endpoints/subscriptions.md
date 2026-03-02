# Subscriptions API Documentation

Endpoints and webhooks for managing user subscriptions and entitlements.

## RevenueCat Webhooks
### `POST /api/v1/webhooks/revenuecat`

Listens for subscription events from RevenueCat to sync entitlement status.

**Request Body (JSON):**
```json
{
  "event": {
    "type": "INITIAL_PURCHASE" | "RENEWAL" | "CANCELLATION",
    "app_user_id": "clerk_id",
    "entitlement_id": "pro",
    "expiration_at_ms": 1234567890
  }
}
```

**Workflow:**
1. Receives webhook from RevenueCat.
2. Updates `subscription_status` and `subscription_expires_at` in the `users` table.

---

## Entitlement Logic

The system checks the user's `subscription_tier` before returning premium content.

### Feature Access Matrix:
| Feature   | Free Tier                 | Pro Tier               |
| :-------- | :------------------------ | :--------------------- |
| Images    | Standard (`url_to_image`) | HD (`url_to_hd_image`) |
| Voices    | Basic Profiles            | High-Quality Profiles  |
| Bookmarks | Max 10                    | Unlimited              |
| Ads       | Included                  | Removed                |
