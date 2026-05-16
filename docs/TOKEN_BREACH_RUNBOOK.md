# Oybit — Token Breach Runbook
(GAPS_FINAL 10.3)

If the Telegram alerter warns of suspicious token usage or a secret key is exposed, execute this runbook immediately.

## 1. Sever Immediate Access
Go to the respective platform developer portal and instantly revoke the exposed Token:
*   **Meta (Facebook/Instagram):** Go to `https://developers.facebook.com/` -> App Dashboard -> Roles -> Revoke all tokens.
*   **LinkedIn:** Go to `https://www.linkedin.com/developers/apps/` -> Auth -> Revoke token.

## 2. Invalidate Internal Storage
Run the database cleanup script to wipe the exposed tokens from PostgreSQL:
```sql
DELETE FROM tokens WHERE account = '[compromised_account]';
```

## 3. Disconnect Worker Loop
If the token refresher is acting maliciously, stop the worker on Railway:
1. Go to Railway dashboard.
2. Select the Backend service.
3. Remove or disable the specific token from the Variables tab.

## 4. Re-Authenticate
1. Navigate back to the local dashboard running in the frontend.
2. Click the "Connect" button for the affected platform.
3. Follow the OAuth flow to generate and store a fresh, uncompromised token.

## 5. Audit
Check the `AuditLog` table for any unauthorized API payloads delivered during the breach window.
