"""
ContentOrbit Enterprise - Main Dashboard Application
=====================================================
Premium UI/UX Dashboard with Setup Wizard for Beginners
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.config_manager import ConfigManager
from core.database_manager import DatabaseManager
from dashboard.auth import check_password, render_logout_button


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def setup_google_credentials():
    """Restores service_account.json from env vars for cloud deployment"""
    import json
    
    # Path relative to project root
    creds_path = ROOT_DIR / "data" / "service_account.json"
    
    if creds_path.exists():
        return

    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        try:
            creds_data = json.loads(creds_json)
            # Ensure data dir exists
            creds_path.parent.mkdir(exist_ok=True, parents=True)
            
            with open(creds_path, "w", encoding="utf-8") as f:
                json.dump(creds_data, f, indent=2)
            print("✅ service_account.json restored from env vars.")
        except Exception as e:
            print(f"❌ Failed to restore credentials: {e}")

setup_google_credentials()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ContentOrbit Enterprise",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM UI/UX CSS - Mobile First Design
# ═══════════════════════════════════════════════════════════════════════════════

def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════


# Support both .env (local) and st.secrets (Streamlit Community)
def get_secret(key: str, default: str = ""):
    """Get secret from either st.secrets or environment"""
    # Try Streamlit secrets first (Streamlit Community Cloud)
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except:
        # Fallback to environment variable
        return os.environ.get(key, default)


DASHBOARD_PASSWORD = get_secret("DASHBOARD_PASSWORD", "admin123")

if not check_password(DASHBOARD_PASSWORD):
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZE MANAGERS
# ═══════════════════════════════════════════════════════════════════════════════


@st.cache_resource
def get_config():
    """Get cached config manager"""
    try:
        return ConfigManager()
    except Exception as e:
        st.error(f"⚠️ Config initialization error: {e}")
        # Return minimal config for dashboard-only mode
        config = ConfigManager()
        config.load(create_if_missing=True)
        return config


@st.cache_resource
def get_db():
    """Get cached database manager"""
    try:
        return DatabaseManager()
    except Exception as e:
        st.warning(f"⚠️ Database unavailable (view-only mode): {e}")
        return None


config = get_config()
db = get_db()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    # Logo/Branding
    brand_name = config.app_config.brand_name
    brand_tagline = config.app_config.brand_tagline

    st.markdown(
        f"""
    <div style="text-align: center; padding: 1.5rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🚀</div>
        <h1 style="
            font-size: 1.5rem; 
            margin: 0;
            background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        ">{brand_name}</h1>
        <p style="color: #a5b4fc; font-size: 0.875rem; margin-top: 0.5rem;">
            {brand_tagline}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        options=[
            "🏠 Home",
            "🚀 Setup Guide",
            "⚙️ Configuration",
            "📡 Sources",
            "🤖 Telegram Bot",
            "📝 Logs",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Quick status
    if db:
        stats = db.get_stats()
    else:
        # Mock stats for view-only mode
        from core.models import SystemStats

        stats = SystemStats(
            total_posts=0,
            active_feeds=len(config.feeds) if config.feeds else 0,
            is_running=False,
            last_post_time=None,
            last_error_time=None,
        )

    # Safely get max_posts_per_day
    max_posts = 10  # default
    if config.app_config.schedule:
        max_posts = config.app_config.schedule.max_posts_per_day

    if stats.is_running:
        st.markdown(
            """
        <div style="
            text-align: center;
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 0.75rem;
        ">
            <span style="color: #10b981; font-weight: 600;">🟢 Bot Running</span>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
        <div style="
            text-align: center;
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid #ef4444;
            border-radius: 12px;
            padding: 0.75rem;
        ">
            <span style="color: #ef4444; font-weight: 600;">🔴 Bot Stopped</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
    <div style="
        text-align: center; 
        margin-top: 0.75rem; 
        color: #a5b4fc; 
        font-size: 0.875rem;
        background: rgba(99, 102, 241, 0.1);
        border-radius: 8px;
        padding: 0.5rem;
    ">
        📊 Posts Today: <strong>{stats.posts_today}/{max_posts}</strong>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Logout button
    render_logout_button()

    # Version & UptimeRobot Link
    st.markdown(
        """
    <div style="text-align: center; margin-top: 2rem;">
        <a href="https://dashboard.uptimerobot.com" target="_blank" style="
            color: #a5b4fc;
            text-decoration: none;
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        ">
            🔗 UptimeRobot Dashboard
        </a>
        <p style="color: #64748b; font-size: 0.75rem; margin-top: 1rem;">
            ContentOrbit v1.0.0<br/>
            Enterprise Edition
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

if page == "🏠 Home":
    from dashboard.views.home import render_home_page

    render_home_page(config, db)

elif page == "🚀 Setup Guide":
    from dashboard.views.setup_guide import render_setup_guide

    render_setup_guide(config, db)

elif page == "⚙️ Configuration":
    from dashboard.views.config_page import render_config_page

    render_config_page(config, db)

elif page == "📡 Sources":
    from dashboard.views.sources import render_sources_page

    render_sources_page(config, db)

elif page == "🤖 Telegram Bot":
    from dashboard.views.telegram_bot import render_telegram_bot_page

    render_telegram_bot_page(config, db)

elif page == "📝 Logs":
    from dashboard.views.logs import render_logs_page

    render_logs_page(config, db)
