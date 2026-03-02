# Technical Specification: Authentication & Profile Layer (Clerk)

This document details the security architecture, authentication flow, and profile management for HyPot-News using **Clerk**.

## 1. Authentication Architecture

We use **Clerk** as our Identity Provider to handle authentication, session management, and user security out-of-the-box.

### Key Benefits:
- **Managed Auth**: Handles password hashing, MFA, and social logins.
- **Cross-Platform**: Seamless integration with Next.js (Web) and Expo/Flutter (Mobile).
- **Security**: Automatic session handling and JWT management.

---

## 2. Backend Integration (FastAPI)

The backend acts as a consumer of Clerk's authentication tokens.

### 2.1 Webhooks (Syncing User Data)
- **`POST /api/v1/webhooks/clerk`**:
    - Listens for `user.created` and `user.updated` events.
    - Syncs Clerk's `user_id` to our PostgreSQL `users` table.
    - Initializes/Updates user preferences (interests, volume) in our database.

### 2.2 Endpoint Protection
- All protected endpoints (e.g., `/news/sync`, `/user/bookmarks`) will validate the **Clerk JWT** in the `Authorization` header.
- **Library**: `python-clerk` or standard JWT validation against Clerk's JWKS.

---

## 3. Frontend Implementation

### Web (Next.js)
- **Components**: Use Clerk's `<SignIn />`, `<SignUp />`, and `<UserButton />` for pre-built, premium UI.
- **Middleware**: Protect routes using Clerk's `clerkMiddleware`.
- **Hooks**: Use `useUser()` and `useAuth()` to manage local session state.

### Mobile (Flutter)
- **Library**: `clerk_flutter` (or specialized HTP client).
- **Flow**: Use Clerk's OAuth/Form flows to authenticate and store a valid session token on the device.

---

## 4. User Data Schema
Refer to [db-schema.md](./db-schema.md#users) for the PostgreSQL structure.

### Profile Mapping:
| Field        | Source                                         |
| :----------- | :--------------------------------------------- |
| `clerk_id`   | Clerk's unique user identifier (`sub` in JWT). |
| `username`   | Pulled from Clerk's profile data.              |
| `email`      | Pulled from Clerk's primary email.             |
| `avatar_url` | Clerk's `image_url`.                           |

---

## 5. Security Measures
- **Managed MFA**: Enabled via the Clerk Dashboard.
- **JWT Validation**: Backend verifies Clerk's signature on every request.
- **CORS**: Clerk handles authorized redirect URIs.
