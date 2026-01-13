# Deploying Dashboard to Streamlit Community Cloud

Streamlit Community Cloud is **free** and perfect for hosting the dashboard separately.

## Prerequisites

1. GitHub account with your repo pushed
2. Streamlit account (free): https://share.streamlit.io/signup

## Deployment Steps

### 1. Prepare Repository

Your repo is already ready! The dashboard is in `dashboard/main_dashboard.py`.

### 2. Deploy on Streamlit Community

1. Go to: https://share.streamlit.io/
2. Click **"New app"**
3. Connect your GitHub repo: `m0shaban/robovai-ContentOrbit`
4. Set these fields:
   - **Branch**: `main`
   - **Main file path**: `dashboard/main_dashboard.py`
   - **App URL**: choose a custom subdomain (e.g., `contentorbit-dashboard`)

5. Click **"Advanced settings"** and add environment variables (Secrets):

```toml
# Paste this in the Secrets section:
ADMIN_USER_ID = "624875667"
DASHBOARD_PASSWORD = "YOUR_PASSWORD"
GROQ_API_KEY = "YOUR_KEY"
TELEGRAM_TOKEN = "YOUR_TOKEN"
CHANNEL_ID = "YOUR_CHANNEL"
DEVTO_API_KEY = "YOUR_KEY"
BLOGGER_BLOG_ID = "YOUR_ID"
BLOGGER_CLIENT_ID = "YOUR_ID"
BLOGGER_CLIENT_SECRET = "YOUR_SECRET"
BLOGGER_REFRESH_TOKEN = "YOUR_TOKEN"
FACEBOOK_PAGE_ID = "YOUR_ID"
FACEBOOK_PAGE_ACCESS_TOKEN = "YOUR_TOKEN"
IMGBB_API_KEY = "YOUR_KEY"
```

6. Click **"Deploy!"**

### 3. Access Dashboard

After deployment (2-3 minutes), you'll get a URL like:
- `https://contentorbit-dashboard.streamlit.app`

⚠️ **Important**: Keep your secrets in Streamlit's Secrets management. Never commit them to GitHub.

## Updating the Dashboard

Any changes you push to `main` branch will auto-deploy to Streamlit Community.

## Free Tier Limits

- Unlimited public apps
- Apps may sleep after inactivity (wake up on first visit)
- Perfect for dashboards (not for 24/7 bots)

## Troubleshooting

If the app fails to start:
1. Check logs in Streamlit dashboard
2. Verify all secrets are set correctly
3. Make sure `dashboard/main_dashboard.py` runs locally first
