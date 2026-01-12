# Deploy Dashboard to Streamlit Community Cloud

## Prerequisites
- GitHub account (free)
- Push your repo to GitHub (private or public)

## Steps

### 1. Push to GitHub
```bash
cd "F:\Raw\robovai ContentOrbit"
git init
git add -A
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<YOU>/<REPO>.git
git push -u origin main
```

### 2. Sign up for Streamlit Community Cloud
- Go to: https://streamlit.io/cloud
- Sign in with GitHub
- Click "New app"

### 3. Configure the app
- **Repository**: select your repo
- **Branch**: `main`
- **Main file path**: `dashboard/main_dashboard.py`
- **App URL**: pick a name like `contentorbit-dashboard`

### 4. Add secrets (CRITICAL)
Click "Advanced settings" → "Secrets"

Paste your environment variables in TOML format:

```toml
ADMIN_USER_ID = "624875667"
TELEGRAM_TOKEN = "your-token-here"
CHANNEL_ID = "-1003547538277"
DASHBOARD_PASSWORD = "6575"
GROQ_API_KEY = "your-key"
DEVTO_API_KEY = "your-key"
BLOGGER_BLOG_ID = "..."
BLOGGER_CLIENT_ID = "..."
BLOGGER_CLIENT_SECRET = "..."
BLOGGER_REFRESH_TOKEN = "..."
FACEBOOK_PAGE_ID = "..."
FACEBOOK_PAGE_ACCESS_TOKEN = "..."
IMGBB_API_KEY = "..."
```

### 5. Deploy
- Click "Deploy"
- Wait 2-3 minutes
- Your dashboard will be live at: `https://<app-name>.streamlit.app`

## Important notes
- Dashboard is **read-only** on Streamlit Community (can view stats, not trigger runs)
- If you want to trigger pipeline from dashboard, bots must be running on Fly.io
- Free tier: sleeps after inactivity (like Render)
- Dashboard password protects access

## Maintenance
- To update: just push to GitHub → Streamlit auto-redeploys
- Secrets stay safe (never committed to git)
