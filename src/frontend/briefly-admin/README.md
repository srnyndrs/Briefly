# Briefly Admin

Admin frontend for Briefly feed/article operations.

## Run Locally

1. Install dependencies:

```bash
npm install
```

2. Create env file from example:

```bash
cp .env.example .env
```

3. Start the app:

```bash
npm start
```

## Scripts

- `npm start`: start dev server.
- `npm test`: run test runner.
- `npm run build`: create production build.

## Environment Variables

- `REACT_APP_API_BASE_URL`: backend API base URL.
- `REACT_APP_USE_DEV_PROXY`: when `true`, API/auth calls use same-origin URLs and are proxied by the dev server.
- `REACT_APP_DEV_PROXY_TARGET`: backend target for proxy mode.

### JWT Dev Bypass (Optional)

Use this only for local/testing environments.

- `REACT_APP_AUTH_BYPASS_ENABLED=true` enables bootstrap logic.
- `REACT_APP_AUTH_ACCESS_TOKEN` and `REACT_APP_AUTH_REFRESH_TOKEN` can be set directly.
- Or provide login/refresh + credentials:
	- `REACT_APP_AUTH_LOGIN_PATH`
	- `REACT_APP_AUTH_REFRESH_PATH`
	- `REACT_APP_AUTH_USERNAME`
	- `REACT_APP_AUTH_PASSWORD`

Behavior:

- If `REACT_APP_AUTH_ACCESS_TOKEN` exists, requests use it immediately.
- Otherwise app attempts login using configured credentials.
- On `401`, app attempts refresh first, then falls back to re-login.

The template lives in `.env.example`.

## CORS in Development

If browser requests to `/auth/login` or feed endpoints fail with CORS:

1. Set `REACT_APP_USE_DEV_PROXY=true`.
2. Set `REACT_APP_DEV_PROXY_TARGET` to your backend URL (for example `http://localhost:8080`).
3. Restart `npm start`.

Proxy routes configured in `src/setupProxy.js`:

- `/auth`
- `/feed`
- `/sources`
- `/me`
