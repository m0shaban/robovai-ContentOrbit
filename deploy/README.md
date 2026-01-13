# ContentOrbit - Quick Deploy Guide (Free Tier)

This is a **temporary setup** optimized for **free hosting** while you prepare to sell the project.

## Architecture (2 Services)

1. **Unified Bot** (Render Free): `main_bot.py` + `telegram_chatbot.py` combined
2. **Dashboard** (Streamlit Community): Separate web interface

---

## 🚀 Part 1: Deploy Unified Bot (Render Free)

### Prerequisites
- GitHub account
- Render account (free): https://render.com/

### Steps

1. **Push Code to GitHub**

```bash
cd "F:\Raw\robovai ContentOrbit"
git add -A
git commit -m "Ready for deployment"
git push origin main
```

2. **Deploy on Render**

- Go to: https://dashboard.render.com/
- Click **"New +"** → **"Web Service"**
- Connect your GitHub repo: `m0shaban/robovai-ContentOrbit`
- Settings:
  - **Name**: `contentorbit-bot`
  - **Region**: Oregon (US West)
  - **Branch**: `main`
  - **Runtime**: Python 3
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `python unified_bot.py`
  - **Instance Type**: Free

3. **Add Environment Variables**

Click "Environment" and add these:

| Key | Value |
|-----|-------|
| `TELEGRAM_TOKEN` | Your Telegram bot token |
| `CHANNEL_ID` | Your Telegram channel ID |
| `ADMIN_USER_ID` | 624875667 |
| `GROQ_API_KEY` | Your Groq API key |
| `DEVTO_API_KEY` | Your Dev.to key |
| `BLOGGER_BLOG_ID` | Your Blogger blog ID |
| `BLOGGER_CLIENT_ID` | Your OAuth client ID |
| `BLOGGER_CLIENT_SECRET` | Your OAuth secret |
| `BLOGGER_REFRESH_TOKEN` | Your refresh token |
| `FACEBOOK_PAGE_ID` | Your FB page ID |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Your FB token |
| `IMGBB_API_KEY` | Your ImgBB key |

4. **Deploy**

Click **"Create Web Service"**. Deployment takes ~5 minutes.

5. **Verify**

- Check logs for: `✅ Bot started successfully`
- Your bot should respond in Telegram

---

## 📊 Part 2: Deploy Dashboard (Streamlit Community)

See: [deploy/streamlit/README.md](streamlit/README.md)

Quick summary:
1. Go to https://share.streamlit.io/
2. Connect GitHub repo
3. Set main file: `dashboard/main_dashboard.py`
4. Add secrets (same env vars as above)
5. Deploy!

---

## ⚠️ Important Notes (Free Tier Limitations)

### Render Free
- ✅ Bot runs 24/7 (as long as health endpoint responds)
- ⚠️ May sleep after 15 min inactivity
- ⚠️ 750 hours/month free (≈31 days if always on)
- 💡 Health endpoint at `/health` keeps it awake

### Streamlit Community
- ✅ Unlimited public apps
- ⚠️ Apps sleep after inactivity
- ⚠️ Wake up on first visit (~10 sec delay)

### Work-around for Sleep
- Set up a free uptime monitor (UptimeRobot.com) to ping `/health` every 5 minutes
- This keeps Render awake during active hours

---

## 🔒 Security Checklist

Before going public:
- [ ] Never commit `.env` (already in `.gitignore`)
- [ ] Use environment variables for all secrets
- [ ] Keep `DASHBOARD_PASSWORD` strong
- [ ] Rotate tokens if they were ever exposed

---

## 📈 Selling the Project

When ready to sell:
1. Transfer GitHub repo ownership
2. Update Render env vars with buyer's keys
3. Update Streamlit secrets
4. Provide access to this deployment guide

---

## 💰 Upgrade Path (for buyer)

After sale, recommend upgrading to:
- **Render Starter** ($7/mo): No sleep, better reliability
- **VPS** (Hetzner €4/mo): Full control, 100% uptime

---

## Support

Logs:
- Render: Dashboard → Logs tab
- Streamlit: App → Manage app → Logs

Common issues:
- Bot not responding: Check Render logs for errors
- Dashboard not loading: Check Streamlit secrets are set
