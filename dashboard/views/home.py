"""
ContentOrbit Enterprise - Home Page
====================================
Premium dashboard home with system status and statistics.
"""

import streamlit as st
from datetime import datetime


def render_home_page(config, db):
    """Render the home/status page"""

    # Header with gradient
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        ">🏠 Dashboard</h1>
        <p style="color: #a5b4fc; font-size: 1.1rem;">
            Welcome to ContentOrbit Enterprise
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Get stats
    stats = db.get_stats()
    config_status = config.get_config_status()
    
    # Schedule config
    schedule = config.app_config.schedule
    max_posts = schedule.max_posts_per_day if schedule else 10
    interval = schedule.posting_interval_minutes if schedule else 60
    start_hour = schedule.active_hours_start if schedule else 8
    end_hour = schedule.active_hours_end if schedule else 23
    timezone = schedule.timezone if schedule else "Africa/Cairo"

    # ═══════════════════════════════════════════════════════════════════════════
    # SYSTEM STATUS BANNER
    # ═══════════════════════════════════════════════════════════════════════════

    if stats.is_running:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
            border: 2px solid #10b981;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        ">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="
                    width: 50px;
                    height: 50px;
                    background: #10b981;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                    animation: pulse 2s infinite;
                ">🟢</div>
                <div>
                    <h3 style="margin: 0; color: #10b981;">Bot is Running</h3>
                    <p style="margin: 0; color: #a5b4fc; font-size: 0.875rem;">
                        Uptime: {stats.system_uptime_hours:.1f} hours
                    </p>
                </div>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; color: #a5b4fc; font-size: 0.875rem;">Next post in</p>
                <p style="margin: 0; color: #10b981; font-size: 1.5rem; font-weight: 700;">~{interval} min</p>
            </div>
        </div>
        <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.7; transform: scale(1.05); }}
            }}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%);
            border: 2px solid #ef4444;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        ">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="
                    width: 50px;
                    height: 50px;
                    background: #ef4444;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                ">🔴</div>
                <div>
                    <h3 style="margin: 0; color: #ef4444;">Bot is Stopped</h3>
                    <p style="margin: 0; color: #a5b4fc; font-size: 0.875rem;">
                        Start the bot to begin automation
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("▶️ Start Bot", type="primary", use_container_width=True, key="start_bot_banner"):
            db.set_bot_running(True)
            st.success("Bot started! Run `python main_bot.py` in terminal to start the worker.")
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # METRICS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("""
    <h2 style="margin-bottom: 1rem;">📊 Today's Statistics</h2>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📝 Posts Today",
            value=stats.posts_today,
            delta=f"of {max_posts} limit",
        )

    with col2:
        st.metric(
            label="📅 This Week", 
            value=stats.posts_this_week
        )

    with col3:
        st.metric(
            label="❌ Errors",
            value=stats.errors_today,
            delta="today" if stats.errors_today > 0 else None,
            delta_color="inverse",
        )

    with col4:
        st.metric(
            label="📋 Queue", 
            value=stats.queue_size
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # PLATFORM STATUS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("""
    <h2 style="margin-bottom: 1rem;">🔌 Connected Platforms</h2>
    """, unsafe_allow_html=True)

    platforms = [
        ("🤖", "Groq AI", config_status.get("groq", False)),
        ("📱", "Telegram", config_status.get("telegram", False)),
        ("📝", "Blogger", config_status.get("blogger", False)),
        ("💻", "Dev.to", config_status.get("devto", False)),
        ("📘", "Facebook", config_status.get("facebook", False)),
    ]

    cols = st.columns(5)
    
    for col, (icon, name, connected) in zip(cols, platforms):
        with col:
            status_class = "connected" if connected else "disconnected"
            status_icon = "✅" if connected else "❌"
            border_color = "#10b981" if connected else "#ef4444"
            bg_color = "rgba(16, 185, 129, 0.1)" if connected else "rgba(239, 68, 68, 0.1)"
            
            st.markdown(f"""
            <div style="
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 16px;
                padding: 1.25rem;
                text-align: center;
                transition: all 0.3s ease;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <p style="font-weight: 600; margin: 0; color: white;">{name}</p>
                <p style="color: {border_color}; font-size: 0.875rem; margin-top: 0.25rem;">
                    {status_icon} {'Connected' if connected else 'Not Set'}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SCHEDULE INFO
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("""
    <h2 style="margin-bottom: 1rem;">⏰ Posting Schedule</h2>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        ">
            <p style="color: #a5b4fc; margin: 0; font-size: 0.875rem;">Interval</p>
            <p style="color: white; font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0;">
                {interval} min
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        ">
            <p style="color: #a5b4fc; margin: 0; font-size: 0.875rem;">Active Hours</p>
            <p style="color: white; font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0;">
                {start_hour}:00 - {end_hour}:00
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        ">
            <p style="color: #a5b4fc; margin: 0; font-size: 0.875rem;">Timezone</p>
            <p style="color: white; font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0;">
                {timezone.split('/')[-1]}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # RECENT POSTS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("""
    <h2 style="margin-bottom: 1rem;">📰 Recent Posts</h2>
    """, unsafe_allow_html=True)

    recent_posts = db.get_recent_posts(limit=5)

    if recent_posts:
        for post in recent_posts:
            status = str(getattr(post, 'status', 'pending')).lower()
            title = getattr(post, 'title_ar', None) or getattr(post, 'title_en', None) or "Untitled"
            created = getattr(post, 'created_at', None)
            
            if status == "published":
                status_color = "#10b981"
                status_icon = "✅"
            elif status == "error":
                status_color = "#ef4444"
                status_icon = "❌"
            else:
                status_color = "#f59e0b"
                status_icon = "⏳"
            
            time_str = ""
            if created:
                if isinstance(created, datetime):
                    time_str = created.strftime("%H:%M")
                else:
                    time_str = str(created)[:5]
            
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 0.5rem;
            ">
                <div style="display: flex; align-items: center; gap: 0.75rem; flex: 1; min-width: 200px;">
                    <span style="
                        background: {status_color}20;
                        color: {status_color};
                        padding: 0.25rem 0.5rem;
                        border-radius: 8px;
                        font-size: 0.875rem;
                    ">{status_icon}</span>
                    <span style="color: white; font-weight: 500;">{title[:60]}{'...' if len(title) > 60 else ''}</span>
                </div>
                <span style="color: #64748b; font-size: 0.875rem;">{time_str}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            background: rgba(99, 102, 241, 0.1);
            border: 1px dashed rgba(99, 102, 241, 0.5);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
        ">
            <p style="font-size: 2rem; margin-bottom: 0.5rem;">📭</p>
            <p style="color: #a5b4fc; margin: 0;">No posts yet</p>
            <p style="color: #64748b; font-size: 0.875rem; margin-top: 0.5rem;">
                Configure your settings and start the bot!
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # QUICK ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("""
    <h2 style="margin-bottom: 1rem;">⚡ Quick Actions</h2>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Reload Config", use_container_width=True, key="reload_config_home"):
            config.reload()
            st.success("Configuration reloaded!")
            st.rerun()

    with col2:
        if st.button("🧹 Clear Old Logs", use_container_width=True, key="clear_logs_home"):
            cleared = db.clear_old_logs(days=7)
            st.success(f"Cleared {cleared} old logs!")

    with col3:
        if stats.is_running:
            if st.button("🛑 Stop Bot", use_container_width=True, type="secondary", key="stop_bot_quick"):
                db.set_bot_running(False)
                st.success("Bot stopped!")
                st.rerun()
        else:
            if st.button("▶️ Start Bot", use_container_width=True, type="primary", key="start_bot_quick"):
                db.set_bot_running(True)
                st.success("Bot started!")
                st.rerun()

    with col4:
        import json
        export_data = {
            "stats": {
                "posts_today": stats.posts_today,
                "posts_this_week": stats.posts_this_week,
                "errors_today": stats.errors_today,
            },
            "config_status": config_status,
        }
        st.download_button(
            label="📊 Export Stats",
            data=json.dumps(export_data, indent=2, default=str),
            file_name="contentorbit_stats.json",
            mime="application/json",
            use_container_width=True,
            key="export_stats_home"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # NEW USER TIP
    # ═══════════════════════════════════════════════════════════════════════════

    if not any(config_status.values()):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%);
            border: 2px solid rgba(99, 102, 241, 0.5);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        ">
            <h3 style="margin-bottom: 0.5rem;">🚀 Getting Started?</h3>
            <p style="color: #a5b4fc; margin-bottom: 1rem;">
                Visit the Setup Guide for step-by-step instructions
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📚 Open Setup Guide", use_container_width=True, type="primary"):
            st.switch_page("pages/setup_guide.py")
