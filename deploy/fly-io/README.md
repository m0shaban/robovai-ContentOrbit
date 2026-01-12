# Deploy Bots to Fly.io (Free Tier)

## Why Fly.io?
- **Better than Render Free**: doesn't sleep as aggressively
- **Free tier**: 3 shared-cpu VMs with 256MB RAM each
- **Always-on**: good for Telegram bots

## Prerequisites
1. Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
2. Sign up: `flyctl auth signup`

## Quick Deploy

### 1. Initialize app
```bash
cd "F:\Raw\robovai ContentOrbit"
flyctl launch --no-deploy
```

When asked:
- App name: `contentorbit-bot` (or anything unique)
- Region: choose closest (e.g., `lhr` for London)
- PostgreSQL? **No**
- Redis? **No**

### 2. Set secrets
```bash
flyctl secrets set TELEGRAM_TOKEN="your-token"
flyctl secrets set CHANNEL_ID="-1003547538277"
flyctl secrets set ADMIN_USER_ID="624875667"
flyctl secrets set GROQ_API_KEY="your-key"
flyctl secrets set DEVTO_API_KEY="your-key"
flyctl secrets set BLOGGER_BLOG_ID="..."
flyctl secrets set BLOGGER_CLIENT_ID="..."
flyctl secrets set BLOGGER_CLIENT_SECRET="..."
flyctl secrets set BLOGGER_REFRESH_TOKEN="..."
flyctl secrets set FACEBOOK_PAGE_ID="..."
flyctl secrets set FACEBOOK_PAGE_ACCESS_TOKEN="..."
flyctl secrets set IMGBB_API_KEY="..."
```

### 3. Deploy
```bash
flyctl deploy
```

### 4. Scale to free tier
```bash
flyctl scale count 1
flyctl scale memory 256
```

## Monitor
```bash
# Logs
flyctl logs

# Status
flyctl status

# SSH into VM
flyctl ssh console
```

## Important notes
- **Free tier limits**: 3 VMs × 256MB
- This config runs **both bots** in one VM via `launcher.py`
- If one bot crashes, the other keeps running
- For 24/7 reliability, keep VM count = 1 (free tier)

## Troubleshooting
If deployment fails:
```bash
flyctl logs --app contentorbit-bot
```

Common issues:
- Out of memory → reduce schedule frequency
- Secrets missing → re-set with `flyctl secrets set`
