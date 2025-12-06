# Authentication Setup Guide

The application now enforces secure authentication using Google OAuth 2.0. Follow these steps to configure it.

## 1. Create Google Cloud Credentials

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Select your project (`mikebrooks` or similar).
3.  Navigate to **APIs & Services** > **Credentials**.
4.  Click **Create Credentials** > **OAuth client ID**.
5.  Select **Web application**.
6.  Set **Authorized redirect URIs**:
    -   `http://localhost:8080` (for Streamlit local)
    -   `http://localhost:8000` (for FastAPI local)
    -   *(Add your deployed URLs here too)*
7.  Click **Create**.
8.  Download the JSON file and save it as `.secrets/client_secret.json`.

## 2. Configure Environment

Alternatively, you can set environment variables:

-   `GOOGLE_CLIENT_ID`: Your Client ID
-   `GOOGLE_CLIENT_SECRET`: Your Client Secret
-   `REDIRECT_URI`: `http://localhost:8080` (or your deployed URL)

## 3. Development Mode Bypass

If you are a developer and want to bypass authentication locally without keys:

1.  Set `ENVIRONMENT=development` in your `.env` file or environment.
2.  Set `ENABLE_AUTH_BYPASS=true` (for API) or click the "Initialize Dev Auth" button on the Streamlit login page.
3.  The app will treat you as `dev@example.com`.

## 4. Troubleshooting

-   **Redirect Mismatch**: Ensure `http://localhost:8080` is exactly what is in the Google Console.
-   **Missing Secrets**: Ensure `.secrets/client_secret.json` exists or env vars are set.
