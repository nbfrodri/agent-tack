---
name: auth
description: Implement authentication and authorization: sessions, OAuth, tokens, MFA and tenant permissions. Use for login, signup, access control or protected routes.
---

# Authentication and authorisation

Auth is where small mistakes become breaches, so the rule is: **don't invent it**. Use the framework's or a mature library's implementation, configure it carefully, and test the failure paths as thoroughly as the happy path.

## Choosing an approach
| Situation | Recommended |
| --- | --- |
| Web app where the frontend and API share a domain (Next.js full stack, Laravel + SPA on the same site) | **Server-side sessions** in an `HttpOnly` cookie |
| SPA or mobile app talking to your own API | Laravel Sanctum, or short-lived access tokens + rotating refresh tokens |
| Server-to-server or third-party API access | API keys (stored hashed, scoped, revocable) or OAuth2 client credentials |
| "Login with Google/GitHub", or enterprise SSO | OAuth2/OIDC through a library, never hand-rolled |
| You'd rather not run auth yourself | A managed provider (Clerk, Auth0, Supabase Auth, Cognito) |

Prefer sessions unless you need stateless tokens: they're revocable by default and avoid many JWT pitfalls.

## Per stack
- **Next.js:** Auth.js (NextAuth) or Better Auth, or a managed provider (Clerk). Check the session in the data-access layer, Server Actions and Route Handlers, not only in middleware.
- **Laravel:** starter kits / Breeze / Fortify for flows, Sanctum for SPA and token auth, Policies and Gates for authorisation, and Socialite for OAuth logins.
- **Python:** Django's built-in auth (+ `django-allauth` for social or MFA); for FastAPI, OAuth2 password/bearer flows with `pwdlib`/`argon2-cffi` and PyJWT, or a provider such as `fastapi-users` or an external IdP.
- **Node:** NestJS with Passport strategies + Guards, or Better Auth / Lucia-style session handling; `argon2` for hashing; `jose` for JWTs.

## Non-negotiables
- **Passwords:** hash with Argon2id (or bcrypt with cost ≥ 12) through the library. Never use MD5/SHA for passwords, and never encrypt them reversibly. Require a minimum length (≥ 8, preferably 12), allow long passphrases, and check them against breached-password lists if possible.
- **Cookies:** `HttpOnly`, `Secure`, `SameSite=Lax` (or `Strict`), a sensible expiry, and session ID rotation on login and privilege change.
- **CSRF:** cookie-based auth needs CSRF protection (framework tokens, or `SameSite` plus Origin checks). Bearer tokens in headers don't.
- **JWTs (if used):** short-lived access tokens (5–15 min); refresh tokens rotated on every use, with reuse detection, stored server-side or in an `HttpOnly` cookie, never in `localStorage`. Verify the signature, `exp`, `iss` and `aud`, pin the algorithm, and never accept `alg: none`.
- **Rate limiting and lockout** on login, signup, password reset and MFA endpoints.
- **No user enumeration:** login and reset responses are the same whether or not the account exists.
- **Reset and verification tokens:** random (≥ 128 bits), single-use, short expiry, stored hashed.
- **Secrets** (signing keys, OAuth client secrets) only in env vars or a secret manager, and rotatable.
- **MFA:** offer TOTP or passkeys (WebAuthn) for sensitive apps, with recovery codes.
- **Logging:** log auth events (login success/failure, password change, role change) without passwords, tokens or full session IDs.

## Authorisation
- Deny by default; check on the server, on every request, at the resource level ("can *this* user edit *this* order?"), not only "is logged in". Hiding a button in the UI is not authorisation.
- Centralise rules in policies or permission functions (`can(user, 'update', order)`) instead of `if user.role == 'admin'` scattered around.
- RBAC (roles → permissions) for most apps; add attribute- or ownership-based checks where resources belong to users or tenants.
- **Multi-tenancy:** every query is scoped by tenant (a global scope, repository filter or Postgres RLS), and tests prove that tenant A can't read tenant B's data.
- **IDOR:** never trust IDs from the client to imply ownership.

## Testing
For every protected endpoint or page, test: unauthenticated → 401 or redirect, authenticated without permission → 403 (or 404), owner/allowed → success, and another user's resource → denied. Also test expired or tampered tokens, reset-token reuse and rate limiting.
