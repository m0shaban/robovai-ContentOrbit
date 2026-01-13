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

st.markdown(
    """
<style>
    /* ═══════════════════════════════════════════════════════════════════════
       ROOT VARIABLES - Premium Color Palette
       ═══════════════════════════════════════════════════════════════════════ */
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --primary-light: #818cf8;
        --secondary: #ec4899;
        --accent: #06b6d4;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --dark: #1e1b4b;
        --dark-secondary: #312e81;
        --light: #f8fafc;
        --glass: rgba(255, 255, 255, 0.1);
        --glass-border: rgba(255, 255, 255, 0.2);
        --shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        --gradient-primary: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        --gradient-dark: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        --gradient-success: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       GLOBAL STYLES
       ═══════════════════════════════════════════════════════════════════════ */
    
    /* Dark Theme Background */
    .stApp {
        background: var(--gradient-dark) !important;
        min-height: 100vh;
    }
    
    .main .block-container {
        padding: 1rem 1rem 3rem 1rem !important;
        max-width: 100% !important;
    }
    
    /* All Text White */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #e2e8f0 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       SIDEBAR - Glassmorphism Design
       ═══════════════════════════════════════════════════════════════════════ */
    
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.1) 100%) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--glass-border) !important;
    }
    
    section[data-testid="stSidebar"] > div {
        padding: 1rem !important;
    }

    /* Keep the sidebar collapse/expand button visible when sidebar is collapsed */
    div[data-testid="stSidebarCollapsedControl"],
    button[data-testid="collapsedControl"] {
        position: fixed !important;
        top: 0.75rem !important;
        left: 0.75rem !important;
        z-index: 99999 !important;
        opacity: 1 !important;
        display: flex !important;
        visibility: visible !important;
        pointer-events: auto !important;
        background: rgba(30, 27, 75, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35) !important;
    }

    button[data-testid="collapsedControl"]:hover {
        border-color: var(--primary) !important;
        transform: translateY(-1px) !important;
    }

    button[data-testid="collapsedControl"] svg {
        fill: #e2e8f0 !important;
    }
    
    /* Sidebar Radio Buttons - Navigation */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 0.5rem !important;
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        padding: 0.875rem 1rem !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(99, 102, 241, 0.3) !important;
        border-color: var(--primary) !important;
        transform: translateX(5px) !important;
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: var(--gradient-primary) !important;
        border-color: transparent !important;
        color: white !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       CARDS & CONTAINERS - Glass Effect
       ═══════════════════════════════════════════════════════════════════════ */
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: var(--glass) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: var(--shadow) !important;
        border-color: var(--primary) !important;
    }
    
    div[data-testid="stMetric"] label {
        color: #a5b4fc !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        color: var(--success) !important;
    }
    
    /* Info/Warning/Error Boxes */
    .stAlert {
        background: var(--glass) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 12px !important;
        border: 1px solid var(--glass-border) !important;
        color: #e2e8f0 !important;
    }
    
    .stAlert > div {
        color: #e2e8f0 !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        padding: 1rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: var(--primary) !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(30, 27, 75, 0.5) !important;
        border: 1px solid var(--glass-border) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 1rem !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       FORM INPUTS - Modern Design
       ═══════════════════════════════════════════════════════════════════════ */
    
    /* Text Inputs */
    .stTextInput > div > div {
        background: rgba(30, 27, 75, 0.8) !important;
        border: 2px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
    }
    
    .stTextInput input {
        color: #ffffff !important;
        background: transparent !important;
    }
    
    .stTextInput input::placeholder {
        color: #94a3b8 !important;
    }
    
    /* Text Area */
    .stTextArea textarea {
        background: rgba(30, 27, 75, 0.8) !important;
        border: 2px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Select Box */
    .stSelectbox > div > div {
        background: rgba(30, 27, 75, 0.8) !important;
        border: 2px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: var(--primary) !important;
    }
    
    /* Number Input */
    .stNumberInput > div > div {
        background: rgba(30, 27, 75, 0.8) !important;
        border: 2px solid var(--glass-border) !important;
        border-radius: 12px !important;
    }
    
    .stNumberInput input {
        color: #ffffff !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       BUTTONS - Premium Style
       ═══════════════════════════════════════════════════════════════════════ */
    
    .stButton > button {
        background: var(--gradient-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Secondary Button */
    .stButton > button[kind="secondary"] {
        background: var(--glass) !important;
        border: 2px solid var(--primary) !important;
        box-shadow: none !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: var(--gradient-success) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       TABS - Modern Design
       ═══════════════════════════════════════════════════════════════════════ */
    
    .stTabs [data-baseweb="tab-list"] {
        background: var(--glass) !important;
        border-radius: 16px !important;
        padding: 0.5rem !important;
        gap: 0.5rem !important;
        border: 1px solid var(--glass-border) !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 12px !important;
        color: #a5b4fc !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.25rem !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        color: white !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-primary) !important;
        color: white !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding: 1.5rem 0 !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       TABLES & DATAFRAMES
       ═══════════════════════════════════════════════════════════════════════ */
    
    .stDataFrame {
        background: var(--glass) !important;
        border-radius: 16px !important;
        border: 1px solid var(--glass-border) !important;
        overflow: hidden !important;
    }
    
    .stDataFrame thead tr th {
        background: rgba(99, 102, 241, 0.3) !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    .stDataFrame tbody tr:hover {
        background: rgba(99, 102, 241, 0.1) !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       MOBILE RESPONSIVE - Full Support
       ═══════════════════════════════════════════════════════════════════════ */
    
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem !important;
        }
        
        /* Stack columns on mobile */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        
        /* Larger touch targets */
        .stButton > button {
            padding: 1rem 1.5rem !important;
            font-size: 1rem !important;
            width: 100% !important;
        }
        
        /* Readable metric cards */
        div[data-testid="stMetric"] {
            padding: 1rem !important;
        }
        
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        /* Tab scrolling */
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            -webkit-overflow-scrolling: touch !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            white-space: nowrap !important;
            padding: 0.5rem 1rem !important;
            font-size: 0.875rem !important;
        }
        
        /* Sidebar collapse friendly */
        section[data-testid="stSidebar"] {
            min-width: 100% !important;
        }
        
        /* Form inputs full width */
        .stTextInput, .stSelectbox, .stNumberInput {
            width: 100% !important;
        }
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       CUSTOM COMPONENTS
       ═══════════════════════════════════════════════════════════════════════ */
    
    /* Setup Step Card */
    .setup-step {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .setup-step:hover {
        border-color: #6366f1;
        transform: translateY(-3px);
    }
    
    .setup-step.completed {
        border-color: #10b981;
        background: rgba(16, 185, 129, 0.1);
    }
    
    .setup-step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        border-radius: 50%;
        color: white;
        font-weight: bold;
        font-size: 1.25rem;
        margin-right: 1rem;
    }
    
    .setup-step.completed .setup-step-number {
        background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
    }
    
    /* Platform Card */
    .platform-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .platform-card:hover {
        transform: translateY(-5px);
        border-color: #6366f1;
    }
    
    .platform-card.connected {
        border-color: #10b981;
        background: rgba(16, 185, 129, 0.1);
    }
    
    .platform-card.disconnected {
        border-color: #ef4444;
        opacity: 0.7;
    }
    
    /* Log Entry */
    .log-entry {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #6366f1;
    }
    
    .log-entry.error {
        border-left-color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
    }
    
    .log-entry.warning {
        border-left-color: #f59e0b;
        background: rgba(245, 158, 11, 0.1);
    }
    
    .log-entry.success {
        border-left-color: #10b981;
        background: rgba(16, 185, 129, 0.1);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e1b4b;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #6366f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #818cf8;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION & SECRETS
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
            successful_posts=0,
            failed_posts=0,
            total_feeds=len(config.feeds) if config.feeds else 0,
            is_running=False,
            last_run=None,
            next_run=None,
            errors_24h=0,
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
