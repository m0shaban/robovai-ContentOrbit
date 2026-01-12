# 🚀 ContentOrbit Enterprise

<div align="center">

![ContentOrbit Logo](https://via.placeholder.com/200x200?text=ContentOrbit)

**Your Content, Everywhere**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io)

</div>

---

## 📋 Overview

**ContentOrbit Enterprise** is a production-grade automated content distribution system. It fetches content from multiple sources, generates AI-enhanced articles, and publishes them across your entire digital ecosystem.

### ✨ Key Features

- 🕷️ **Spider Web Strategy**: Create content hubs (Blogger, Dev.to) and distribute through spokes (Telegram, Facebook)
- 🤖 **AI-Powered**: Uses Groq's Llama 3.1 for intelligent content generation
- ⚙️ **Config-Driven**: Same code, different clients - just change the configuration
- 📊 **Admin Dashboard**: Beautiful Streamlit interface for monitoring and management
- 🔄 **24/7 Automation**: Runs continuously with APScheduler
- 🛡️ **Duplicate Prevention**: Smart URL hashing to avoid re-posting

---

## 🏗️ Architecture

```
ContentOrbit Enterprise/
├── 📁 core/                    # The Logic Core
│   ├── 📁 fetcher/            # RSS parsing
│   ├── 📁 publisher/          # Platform integrations
│   ├── 📁 ai_engine/          # LLM client
│   ├── models.py              # Pydantic data models
│   ├── config_manager.py      # Configuration system
│   └── database_manager.py    # SQLite persistence
├── 📁 dashboard/              # Streamlit components
├── 📁 data/                   # Database & logs
│   ├── contentorbit.db        # SQLite database
│   ├── config.json            # System configuration
│   ├── feeds.json             # RSS feeds list
│   └── 📁 logs/               # Execution logs
├── main_bot.py                # Background worker entry
├── main_dashboard.py          # Dashboard entry
├── requirements.txt           # Dependencies
└── .env.example               # Environment template
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/your-org/contentorbit.git
cd contentorbit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
notepad .env  # or use your preferred editor
```

### 3. Run the System

```bash
# Terminal 1: Start the Bot Worker
python main_bot.py

# Terminal 2: Start the Dashboard
streamlit run main_dashboard.py
```

---

## ⚙️ Configuration

### Required API Keys

| Platform     | Required    | How to Get                                                       |
| ------------ | ----------- | ---------------------------------------------------------------- |
| **Groq**     | ✅ Yes      | [console.groq.com](https://console.groq.com)                     |
| **Telegram** | ✅ Yes      | [@BotFather](https://t.me/BotFather)                             |
| **Blogger**  | ⭕ Optional | [Google Cloud Console](https://console.cloud.google.com)         |
| **Dev.to**   | ⭕ Optional | [dev.to/settings/extensions](https://dev.to/settings/extensions) |
| **Facebook** | ⭕ Optional | [Meta Developer Portal](https://developers.facebook.com)         |

### Dashboard Configuration

Access the dashboard at `http://localhost:8501` to:

- Edit API keys securely
- Manage RSS feeds (100+ supported)
- Customize AI prompts (persona)
- Set posting schedule
- Monitor logs and stats

---

## 📡 The Spider Web Strategy

```
                     ┌─────────────────┐
                     │   RSS Sources   │
                     │  (100+ feeds)   │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   AI Engine     │
                     │  (Groq/Llama)   │
                     └────────┬────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌───────────┐   ┌───────────┐   ┌───────────┐
      │  Blogger  │   │  Dev.to   │   │   (Hub)   │
      │   (Hub)   │   │  (Tech)   │   │           │
      └─────┬─────┘   └─────┬─────┘   └───────────┘
            │               │
            └───────┬───────┘
                    ▼
      ┌─────────────────────────────┐
      │      Social Distribution    │
      │   ┌──────────┬──────────┐   │
      │   │ Telegram │ Facebook │   │
      │   │ (Spokes) │ (Spokes) │   │
      │   └──────────┴──────────┘   │
      └─────────────────────────────┘
```

---

## 🐳 Docker Deployment

```bash
# Build the image
docker build -t contentorbit .

# Run with environment file
docker run -d --env-file .env -p 8501:8501 contentorbit
```

---

## 🏢 White-Label Usage

ContentOrbit is designed for **multi-tenant deployment**:

1. **Clone** the repository for each client
2. **Configure** their unique API keys and feeds
3. **Deploy** to their Render/Railway instance
4. **Hand over** dashboard access

Each client gets their own:

- Telegram channel
- Blogger/website
- Content sources
- AI persona

---

## 📄 License

MIT License - Feel free to use commercially.

---

## 🤝 Support

- 📧 Email: support@contentorbit.io
- 💬 Telegram: @ContentOrbitSupport
- 📚 Docs: [docs.contentorbit.io](https://docs.contentorbit.io)

---

<div align="center">

**Built with ❤️ for Content Creators**

</div>
