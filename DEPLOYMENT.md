# 🚀 ContentOrbit Enterprise

## Production-Grade Content Automation Platform

<div align="center">

![ContentOrbit](https://img.shields.io/badge/ContentOrbit-Enterprise-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Config-Driven • White-Label Ready • Multi-Platform Publishing**

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Deployment](#-deployment)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [White-Label Setup](#-white-label-setup)
- [Troubleshooting](#-troubleshooting)

---

## 🌟 Overview

ContentOrbit Enterprise is a **production-ready SaaS platform** for automated content distribution. It follows the "Spider Web Strategy" - fetch content from multiple RSS sources, transform it using AI, and publish across multiple platforms simultaneously.

### The Spider Web Strategy

```
                    📡 RSS Sources
                         │
                    ┌────┴────┐
                    │   🕷️    │
                    │ Fetch   │
                    └────┬────┘
                         │
                    ┌────┴────┐
                    │   🤖    │
                    │ AI/LLM  │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
   │ Blogger │     │ Dev.to  │     │Telegram │
   │ (Arabic)│     │(English)│     │ (Both)  │
   └─────────┘     └─────────┘     └─────────┘
```

---

## ✨ Features

### Core Capabilities

| Feature                  | Description                                |
| ------------------------ | ------------------------------------------ |
| 🔄 **Multi-Source RSS**  | Aggregate content from unlimited RSS feeds |
| 🤖 **AI Transformation** | Groq LLM for intelligent content rewriting |
| 🌐 **Multi-Platform**    | Blogger, Dev.to, Telegram, Facebook        |
| 🎨 **White-Label**       | Full branding customization                |
| ⚙️ **Config-Driven**     | Change everything without touching code    |
| 📊 **Dashboard**         | Beautiful Streamlit admin UI               |
| 🔒 **Secure**            | Password-protected, OAuth2 support         |
| 🐳 **Docker Ready**      | One-command deployment                     |

### Platform Support

- **📝 Blogger** - Arabic SEO articles with auto-labels
- **💻 Dev.to** - English technical articles with tags
- **📱 Telegram** - Channel posts with formatting
- **📘 Facebook** - Page posts with hashtags

---

## 🏗️ Architecture

```
contentorbit/
├── 📁 core/                    # Business Logic
│   ├── models.py              # Pydantic data models
│   ├── config_manager.py      # Config-driven architecture
│   ├── database_manager.py    # SQLite persistence
│   ├── content_orchestrator.py # Main pipeline coordinator
│   ├── 📁 fetcher/
│   │   └── rss_parser.py      # Async RSS fetching
│   ├── 📁 ai_engine/
│   │   ├── llm_client.py      # Groq integration
│   │   └── prompt_manager.py  # Prompt templates
│   └── 📁 publisher/
│       ├── blogger_publisher.py
│       ├── devto_publisher.py
│       ├── telegram_publisher.py
│       └── facebook_publisher.py
│
├── 📁 dashboard/               # Streamlit Admin UI
│   ├── main_dashboard.py      # Entry point
│   ├── components.py          # Reusable UI components
│   ├── auth.py                # Authentication
│   └── 📁 pages/
│       ├── home.py            # Status & metrics
│       ├── config_page.py     # Settings management
│       ├── sources.py         # RSS feed management
│       └── logs.py            # Execution logs
│
├── 📁 data/                    # Persistent Storage
│   ├── config.json            # Main configuration
│   ├── feeds.json             # RSS feeds list
│   ├── contentorbit.db        # SQLite database
│   └── 📁 logs/
│       └── bot.log
│
├── main_bot.py                # Background worker
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── render.yaml                # Render.com config
└── start.sh                   # Startup script
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### Local Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/contentorbit.git
cd contentorbit

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create data directory
mkdir -p data/logs

# 5. Start the dashboard
streamlit run dashboard/main_dashboard.py
```

### First-Time Setup

1. Open http://localhost:8501
2. Login with default password: `admin123`
3. Go to **Configuration** → **API Keys**
4. Enter your Groq API key
5. Go to **Sources** → Add RSS feeds
6. Go to **Home** → Click **Start Bot**
7. Run the worker: `python main_bot.py`

---

## 🐳 Deployment

### Docker (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Render.com (One-Click)

1. Fork this repository
2. Create new **Blueprint** on Render
3. Connect your GitHub repo
4. Set environment variables in Render dashboard
5. Deploy!

### Manual VPS Deployment

```bash
# Using the startup script
chmod +x start.sh

# Install and setup
./start.sh setup

# Start all services
./start.sh start

# Check status
./start.sh status

# Stop all
./start.sh stop
```

### Environment Variables

| Variable              | Description                | Required |
| --------------------- | -------------------------- | -------- |
| `DASHBOARD_PASSWORD`  | Dashboard login password   | Yes      |
| `GROQ_API_KEY`        | Groq AI API key            | Yes      |
| `TELEGRAM_BOT_TOKEN`  | Telegram bot token         | No       |
| `BLOGGER_CLIENT_ID`   | Google OAuth2 client ID    | No       |
| `DEVTO_API_KEY`       | Dev.to API key             | No       |
| `FACEBOOK_PAGE_TOKEN` | Facebook page access token | No       |

---

## ⚙️ Configuration

### Config File Structure

All settings are stored in `data/config.json`:

```json
{
  "schedule": {
    "posting_interval_minutes": 30,
    "max_posts_per_day": 10,
    "active_hours_start": 8,
    "active_hours_end": 22,
    "timezone": "UTC"
  },
  "groq": {
    "api_key": "gsk_...",
    "model": "llama-3.1-70b-versatile"
  },
  "prompts": {
    "blogger_prompt": "...",
    "devto_prompt": "...",
    "telegram_prompt": "...",
    "facebook_prompt": "..."
  },
  "branding": {
    "bot_name": "ContentOrbit",
    "tagline": "Automate Your Content",
    "primary_color": "#4F46E5",
    "logo_url": null
  }
}
```

### RSS Feeds Format

Feeds are stored in `data/feeds.json`:

```json
[
  {
    "name": "TechCrunch AI",
    "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "category": "AI",
    "language": "en",
    "enabled": true
  }
]
```

---

## 🎨 White-Label Setup

ContentOrbit is designed for white-label deployment. Each client gets:

1. **Custom Branding** - Name, colors, logo
2. **Isolated Config** - Separate `data/` directory
3. **Same Codebase** - No code changes needed

### Multi-Tenant Deployment

```bash
# Client A
DATA_DIR=/data/client-a docker-compose up -d

# Client B
DATA_DIR=/data/client-b docker-compose up -d
```

### Branding Customization

Via Dashboard → Configuration → Branding:

- Bot Name
- Tagline
- Primary/Secondary Colors
- Logo URL

---

## 🔧 Troubleshooting

### Common Issues

| Issue                 | Solution                                  |
| --------------------- | ----------------------------------------- |
| "Bot not starting"    | Check if `is_running` is true in database |
| "No posts publishing" | Verify API keys in Configuration          |
| "RSS feed errors"     | Test feed URL in Sources page             |
| "LLM timeout"         | Check Groq API status                     |

### Logs Location

- Bot logs: `data/logs/bot.log`
- Dashboard logs: Streamlit console output
- Database logs: `SELECT * FROM system_logs`

### Reset Everything

```bash
# Clear all data
rm -rf data/*
mkdir -p data/logs

# Restart
./start.sh start
```

---

## 📄 License

MIT License - Feel free to use for commercial projects.

---

## 🤝 Support

- 📧 Email: support@contentorbit.io
- 💬 Telegram: @ContentOrbitSupport
- 📖 Docs: https://docs.contentorbit.io

---

<div align="center">

**Built with ❤️ for Content Creators**

[⬆ Back to Top](#-contentorbit-enterprise)

</div>
