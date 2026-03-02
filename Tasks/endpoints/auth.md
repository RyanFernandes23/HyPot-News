# Auth API Documentation

Documentation for authentication-related endpoints and webhooks.

## Clerk Webhooks

### `POST /api/v1/webhooks/clerk`

Syncs user data from Clerk to our internal database on user creation or update events.

**Request Headers:**
- `clerk-signature`: Signature for webhook verification.

**Request Body (JSON):**
```json
{
  "data": {
    "id": "user_...",
    "username": "jdoe",
    "email_addresses": [...],
    "image_url": "..."
  },
  "type": "user.created" | "user.updated"
}
```

**Workflow:**
1. Receives webhook from Clerk.
2. Validates signature.
3. Syncs `clerk_id` to PostgreSQL `users` table.
4. Initializes or updates user preferences.

**Security:**
- Verified using Clerk's public key (JWKS) or webhook secret.
