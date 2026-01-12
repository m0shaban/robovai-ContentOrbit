"""
ContentOrbit Enterprise - Setup Guide Page
==========================================
Step-by-step guide for beginners to configure the system.
"""

import streamlit as st


def render_setup_guide(config, db):
    """Render the setup guide for beginners"""

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        ">🚀 Setup Guide</h1>
        <p style="color: #a5b4fc; font-size: 1.1rem;">
            Follow these steps to get ContentOrbit running in minutes
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Check current configuration status
    config_status = config.get_config_status()
    
    # Calculate progress
    total_steps = 5
    completed_steps = sum([
        config_status.get("groq", False),
        config_status.get("telegram", False) or config_status.get("blogger", False),
        len(config.feeds or []) > 0,
        True,  # Schedule is always configured by default
        db.get_stats().is_running
    ])
    
    progress = completed_steps / total_steps

    # Progress bar
    st.markdown(f"""
    <div style="
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    ">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
            <span style="color: #a5b4fc; font-weight: 600;">Setup Progress</span>
            <span style="color: #10b981; font-weight: 700;">{int(progress * 100)}% Complete</span>
        </div>
        <div style="
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            height: 12px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
                height: 100%;
                width: {progress * 100}%;
                border-radius: 8px;
                transition: width 0.5s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1: Groq AI Setup
    # ═══════════════════════════════════════════════════════════════════════════
    
    groq_done = config_status.get("groq", False)
    
    st.markdown(f"""
    <div class="setup-step {'completed' if groq_done else ''}">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="setup-step-number">{'✓' if groq_done else '1'}</div>
            <div>
                <h3 style="margin: 0; font-size: 1.25rem;">Get Groq AI API Key</h3>
                <p style="margin: 0; color: #a5b4fc; font-size: 0.875rem;">Required for content generation</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 How to get Groq API Key" if not groq_done else "✅ Groq AI Configured!", expanded=not groq_done):
        st.markdown("""
        ### Steps:
        
        1. **Go to Groq Console:**
           - Open: [console.groq.com](https://console.groq.com)
           - Create a free account if you don't have one
        
        2. **Create API Key:**
           - Click on "API Keys" in the sidebar
           - Click "Create API Key"
           - Copy the key (starts with `gsk_...`)
        
        3. **Add to ContentOrbit:**
           - Go to **⚙️ Configuration** page
           - Paste your API key in the Groq section
           - Click "Save Groq Settings"
        
        ### 🎁 Free Tier:
        - **Free:** 30 requests/minute
        - **Models:** Llama 3.1 70B, Mixtral 8x7B
        - **No credit card required!**
        """)
        
        st.link_button("🔗 Open Groq Console", "https://console.groq.com", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2: Platform Setup
    # ═══════════════════════════════════════════════════════════════════════════
    
    any_platform = config_status.get("telegram", False) or config_status.get("blogger", False) or config_status.get("devto", False)
    
    st.markdown(f"""
    <div class="setup-step {'completed' if any_platform else ''}">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="setup-step-number">{'✓' if any_platform else '2'}</div>
            <div>
                <h3 style="margin: 0; font-size: 1.25rem;">Connect Publishing Platforms</h3>
                <p style="margin: 0; color: #a5b4fc; font-size: 0.875rem;">At least one platform required</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 Platform Setup Guides" if not any_platform else "✅ Platform Connected!", expanded=not any_platform):
        
        platform_tab1, platform_tab2, platform_tab3, platform_tab4 = st.tabs([
            "📱 Telegram",
            "📝 Blogger", 
            "💻 Dev.to",
            "📘 Facebook"
        ])
        
        with platform_tab1:
            st.markdown("""
            ### Telegram Bot Setup (Easiest!)
            
            1. **Create Bot:**
               - Open Telegram and search for [@BotFather](https://t.me/BotFather)
               - Send `/newbot` and follow instructions
               - Copy the **Bot Token** (looks like `123456:ABC-DEF...`)
            
            2. **Get Channel ID:**
               - Create a channel or use existing one
               - Add your bot as **Admin** to the channel
               - Forward any message from channel to [@userinfobot](https://t.me/userinfobot)
               - Copy the **Channel ID** (starts with `-100...`)
            
            3. **Configure:**
               - Go to **⚙️ Configuration** → Telegram
               - Enter Bot Token & Channel ID
               - Save settings
            
            ⏱️ **Time:** ~3 minutes
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("🤖 Open BotFather", "https://t.me/BotFather", use_container_width=True)
            with col2:
                st.link_button("ℹ️ UserInfo Bot", "https://t.me/userinfobot", use_container_width=True)
        
        with platform_tab2:
            st.markdown("""
            ### Blogger Setup (Google Account Required)
            
            1. **Create Blog:**
               - Go to [blogger.com](https://www.blogger.com)
               - Create a new blog or use existing
            
            2. **Get Blog ID:**
               - Open your blog dashboard
               - Look at URL: `blogger.com/blog/posts/BLOG_ID`
               - Copy the **BLOG_ID** number
            
            3. **Create OAuth Credentials:**
               - Go to [Google Cloud Console](https://console.cloud.google.com)
               - Create new project
               - Enable Blogger API
               - Create OAuth 2.0 credentials
               - Download JSON file
            
            4. **Get Refresh Token:**
               - Use the OAuth playground or our setup script
               - Enter Client ID, Secret, and authorize
               - Copy the **Refresh Token**
            
            ⏱️ **Time:** ~15 minutes
            """)
            
            st.link_button("📝 Open Blogger", "https://www.blogger.com", use_container_width=True)
        
        with platform_tab3:
            st.markdown("""
            ### Dev.to Setup (Simplest API!)
            
            1. **Get API Key:**
               - Go to [dev.to/settings/extensions](https://dev.to/settings/extensions)
               - Scroll to "DEV API Keys"
               - Generate new key with description
               - Copy the **API Key**
            
            2. **Configure:**
               - Go to **⚙️ Configuration** → Dev.to
               - Paste your API Key
               - Save settings
            
            ⏱️ **Time:** ~1 minute
            """)
            
            st.link_button("💻 Open Dev.to Settings", "https://dev.to/settings/extensions", use_container_width=True)
        
        with platform_tab4:
            st.markdown("""
            ### Facebook Page Setup
            
            1. **Create Facebook Page** (if needed)
            
            2. **Get Page Access Token:**
               - Go to [Facebook Developers](https://developers.facebook.com)
               - Create an App
               - Add Facebook Login product
               - Get User Token from Graph API Explorer
               - Exchange for Long-Lived Page Token
            
            3. **Get Page ID:**
               - Go to your Page → About
               - Scroll to Page ID
            
            ⏱️ **Time:** ~20 minutes
            """)
            
            st.link_button("📘 Facebook Developers", "https://developers.facebook.com", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3: Add RSS Feeds
    # ═══════════════════════════════════════════════════════════════════════════
    
    feeds_done = len(config.feeds or []) > 0
    
    st.markdown(f"""
    <div class="setup-step {'completed' if feeds_done else ''}">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="setup-step-number">{'✓' if feeds_done else '3'}</div>
            <div>
                <h3 style="margin: 0; font-size: 1.25rem;">Add Content Sources (RSS)</h3>
                <p style="margin: 0; color: #a5b4fc; font-size: 0.875rem;">Where to fetch articles from</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 Adding RSS Feeds" if not feeds_done else f"✅ {len(config.feeds or [])} Feeds Added!", expanded=not feeds_done):
        st.markdown("""
        ### What are RSS Feeds?
        
        RSS feeds are automatic content streams from websites. When a site publishes new articles, they appear in the RSS feed.
        
        ### How to Add Feeds:
        
        1. Go to **📡 Sources** page
        2. Click "Add New Feed" in sidebar
        3. Enter:
           - **Name:** e.g., "TechCrunch"
           - **URL:** RSS feed URL
           - **Category:** tech, business, etc.
        
        ### Popular Tech RSS Feeds:
        
        | Source | RSS URL |
        |--------|---------|
        | TechCrunch | `https://techcrunch.com/feed/` |
        | The Verge | `https://www.theverge.com/rss/index.xml` |
        | Wired | `https://www.wired.com/feed/rss` |
        | Ars Technica | `https://feeds.arstechnica.com/arstechnica/technology-lab` |
        | Hacker News | `https://hnrss.org/frontpage` |
        
        ### Finding RSS for Any Site:
        
        1. Look for 🔗 RSS icon on the site
        2. Try adding `/feed/` or `/rss` to the URL
        3. Use [RSS.app](https://rss.app) to create feeds
        """)
        
        if st.button("📡 Go to Sources Page", use_container_width=True):
            st.switch_page("pages/sources.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4: Configure Schedule
    # ═══════════════════════════════════════════════════════════════════════════
    
    st.markdown("""
    <div class="setup-step completed">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="setup-step-number">✓</div>
            <div>
                <h3 style="margin: 0; font-size: 1.25rem;">Configure Posting Schedule</h3>
                <p style="margin: 0; color: #a5b4fc; font-size: 0.875rem;">Default schedule is ready!</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 Customize Schedule (Optional)"):
        schedule = config.app_config.schedule
        if schedule:
            st.markdown(f"""
            ### Current Schedule:
            
            - **Posting Interval:** Every {schedule.posting_interval_minutes} minutes
            - **Active Hours:** {schedule.active_hours_start}:00 - {schedule.active_hours_end}:00
            - **Max Posts/Day:** {schedule.max_posts_per_day}
            - **Timezone:** {schedule.timezone}
            
            ### Recommendations:
            
            | Use Case | Interval | Max Posts |
            |----------|----------|-----------|
            | Personal Blog | 120 min | 5/day |
            | News Site | 30 min | 20/day |
            | Tech Channel | 60 min | 10/day |
            
            Go to **⚙️ Configuration** → **Schedule** tab to customize.
            """)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 5: Start the Bot
    # ═══════════════════════════════════════════════════════════════════════════
    
    is_running = db.get_stats().is_running
    
    st.markdown(f"""
    <div class="setup-step {'completed' if is_running else ''}">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="setup-step-number">{'✓' if is_running else '5'}</div>
            <div>
                <h3 style="margin: 0; font-size: 1.25rem;">Start ContentOrbit Bot</h3>
                <p style="margin: 0; color: #a5b4fc; font-size: 0.875rem;">Launch the automation!</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 Starting the Bot" if not is_running else "✅ Bot is Running!", expanded=not is_running):
        st.markdown("""
        ### Running Locally:
        
        ```bash
        # In terminal/command prompt:
        cd /path/to/contentorbit
        python main_bot.py
        ```
        
        ### Running on Server (24/7):
        
        **Option 1: Docker (Recommended)**
        ```bash
        docker-compose up -d
        ```
        
        **Option 2: systemd (Linux)**
        ```bash
        sudo systemctl start contentorbit
        ```
        
        **Option 3: PM2 (Node.js Process Manager)**
        ```bash
        pm2 start "python main_bot.py" --name contentorbit
        ```
        
        ### Cloud Deployment:
        
        - **Render.com** - Free tier available
        - **Railway.app** - Easy deployment
        - **DigitalOcean** - $5/month droplet
        
        ### Monitoring with UptimeRobot:
        
        1. Go to [UptimeRobot](https://dashboard.uptimerobot.com)
        2. Add new monitor
        3. Monitor type: HTTP(s)
        4. Enter your dashboard URL
        5. Get alerts when bot goes down!
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Bot" if not is_running else "🔄 Restart Bot", use_container_width=True, type="primary"):
                db.set_bot_running(True)
                st.success("Bot started! Run `python main_bot.py` in terminal.")
                st.rerun()
        with col2:
            st.link_button("🔗 UptimeRobot", "https://dashboard.uptimerobot.com", use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # Quick Links
    # ═══════════════════════════════════════════════════════════════════════════
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    <h3 style="text-align: center; margin-bottom: 1.5rem;">🔗 Quick Links</h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="platform-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
            <p style="font-weight: 600; margin: 0;">Groq Console</p>
            <a href="https://console.groq.com" target="_blank" style="color: #a5b4fc; font-size: 0.875rem;">
                console.groq.com
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="platform-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📱</div>
            <p style="font-weight: 600; margin: 0;">BotFather</p>
            <a href="https://t.me/BotFather" target="_blank" style="color: #a5b4fc; font-size: 0.875rem;">
                t.me/BotFather
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="platform-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">💻</div>
            <p style="font-weight: 600; margin: 0;">Dev.to</p>
            <a href="https://dev.to/settings/extensions" target="_blank" style="color: #a5b4fc; font-size: 0.875rem;">
                dev.to/settings
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="platform-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <p style="font-weight: 600; margin: 0;">UptimeRobot</p>
            <a href="https://dashboard.uptimerobot.com" target="_blank" style="color: #a5b4fc; font-size: 0.875rem;">
                uptimerobot.com
            </a>
        </div>
        """, unsafe_allow_html=True)

    # Help section
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
    ">
        <h3 style="margin-bottom: 1rem;">🆘 Need Help?</h3>
        <p style="color: #a5b4fc; margin-bottom: 1rem;">
            Check the logs page for errors or contact support
        </p>
        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
            <a href="https://github.com/your-repo/contentorbit/issues" target="_blank" style="
                background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
            ">📝 Report Issue</a>
            <a href="https://github.com/your-repo/contentorbit/wiki" target="_blank" style="
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
            ">📚 Documentation</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
