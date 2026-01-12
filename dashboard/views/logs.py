"""
ContentOrbit Enterprise - Logs Page
===================================
Premium log viewer with filtering and real-time updates.
"""

import streamlit as st
from datetime import datetime, timedelta

from dashboard.components import render_log_entry


def render_logs_page(config, db):
    """Render the logs viewer page"""

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        ">📝 System Logs</h1>
        <p style="color: #a5b4fc; font-size: 1.1rem;">
            Monitor execution history and system events
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # FILTERS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h4 style="margin: 0 0 1rem 0; color: #a5b4fc;">🔍 Filters</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        level_filter = st.selectbox(
            "Log Level",
            options=["All", "INFO", "WARNING", "ERROR", "SUCCESS"],
            key="log_level_filter",
        )

    with col2:
        component_filter = st.selectbox(
            "Component",
            options=[
                "All",
                "orchestrator",
                "rss_parser",
                "llm_client",
                "blogger",
                "devto",
                "telegram",
                "facebook",
                "scheduler",
                "bot",
            ],
            key="log_component_filter",
        )

    with col3:
        time_filter = st.selectbox(
            "Time Range",
            options=["Last Hour", "Last 24 Hours", "Last 7 Days", "All Time"],
            index=1,
            key="log_time_filter",
        )

    with col4:
        limit = st.number_input(
            "Max Results",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="log_limit",
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # FETCH LOGS
    # ═══════════════════════════════════════════════════════════════════════════

    # Build filter params
    filter_level = None if level_filter == "All" else level_filter.lower()
    filter_component = None if component_filter == "All" else component_filter

    # Time filter
    if time_filter == "Last Hour":
        since = datetime.now() - timedelta(hours=1)
    elif time_filter == "Last 24 Hours":
        since = datetime.now() - timedelta(days=1)
    elif time_filter == "Last 7 Days":
        since = datetime.now() - timedelta(days=7)
    else:
        since = None

    # Get logs from database
    logs = db.get_logs(
        limit=limit, level=filter_level, component=filter_component, since=since
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # STATS SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════

    if logs:
        # Count by level - handle both Pydantic models and dicts
        def get_level(log):
            if hasattr(log, 'level'):
                level_str = str(log.level).lower()
            else:
                level_str = str(log.get('level', 'info')).lower()
            # Remove 'loglevel.' prefix if present
            if level_str.startswith("loglevel."):
                level_str = level_str.replace("loglevel.", "")
            return level_str
        
        info_count = len([l for l in logs if get_level(l) == "info"])
        warning_count = len([l for l in logs if get_level(l) == "warning"])
        error_count = len([l for l in logs if get_level(l) == "error"])
        success_count = len([l for l in logs if get_level(l) == "success"])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
            ">
                <p style="color: #a5b4fc; margin: 0; font-size: 0.875rem;">ℹ️ Info</p>
                <p style="color: #6366f1; font-size: 2rem; font-weight: 700; margin: 0.25rem 0;">{info_count}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div style="
                background: rgba(245, 158, 11, 0.1);
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
            ">
                <p style="color: #fbbf24; margin: 0; font-size: 0.875rem;">⚠️ Warnings</p>
                <p style="color: #f59e0b; font-size: 2rem; font-weight: 700; margin: 0.25rem 0;">{warning_count}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div style="
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
            ">
                <p style="color: #f87171; margin: 0; font-size: 0.875rem;">❌ Errors</p>
                <p style="color: #ef4444; font-size: 2rem; font-weight: 700; margin: 0.25rem 0;">{error_count}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div style="
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
            ">
                <p style="color: #34d399; margin: 0; font-size: 0.875rem;">✅ Success</p>
                <p style="color: #10b981; font-size: 2rem; font-weight: 700; margin: 0.25rem 0;">{success_count}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # VIEW MODE
    # ═══════════════════════════════════════════════════════════════════════════

    view_mode = st.radio(
        "View Mode",
        options=["📋 Cards", "📊 Table", "🔍 Raw"],
        horizontal=True,
        key="logs_view_mode",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # DISPLAY LOGS
    # ═══════════════════════════════════════════════════════════════════════════

    if not logs:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 2px dashed rgba(99, 102, 241, 0.5);
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
            <h3 style="color: white; margin-bottom: 0.5rem;">No Logs Found</h3>
            <p style="color: #a5b4fc;">Try adjusting your filters or wait for new activity</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"""
    <p style="color: #64748b; margin-bottom: 1rem;">
        Showing <strong style="color: #a5b4fc;">{len(logs)}</strong> log entries
    </p>
    """, unsafe_allow_html=True)

    # Helper to get log attributes
    def get_attr(log, attr, default=""):
        if hasattr(log, attr):
            return getattr(log, attr, default)
        return log.get(attr, default)

    if view_mode == "📋 Cards":
        # Card view with styled entries
        for log in logs:
            render_log_entry(log)

    elif view_mode == "📊 Table":
        # Table view
        import pandas as pd
        
        logs_data = []
        for log in logs:
            timestamp = get_attr(log, 'timestamp', None)
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            elif timestamp:
                timestamp = str(timestamp)
            else:
                timestamp = "-"
                
            level = str(get_attr(log, 'level', 'info'))
            if level.lower().startswith("loglevel."):
                level = level.split(".")[-1]
                
            message = get_attr(log, 'message', '')
            if len(message) > 80:
                message = message[:80] + "..."
                
            logs_data.append({
                "Time": timestamp,
                "Level": level.upper(),
                "Component": get_attr(log, 'component', '-'),
                "Message": message
            })

        df = pd.DataFrame(logs_data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Time": st.column_config.TextColumn("Time", width="medium"),
                "Level": st.column_config.TextColumn("Level", width="small"),
                "Component": st.column_config.TextColumn("Component", width="small"),
                "Message": st.column_config.TextColumn("Message", width="large")
            }
        )

    else:
        # Raw view
        raw_logs = []
        for log in logs:
            timestamp = get_attr(log, 'timestamp', None)
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp = str(timestamp) if timestamp else "-"
            component = get_attr(log, 'component', 'system')
            level = str(get_attr(log, 'level', 'info')).upper()
            if level.startswith("LOGLEVEL."):
                level = level.split(".")[-1]
            message = get_attr(log, 'message', '')
            raw_logs.append(f"[{timestamp}] [{level}] [{component}] {message}")
        
        st.code("\n".join(raw_logs), language="text")

    # ═══════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    <h3 style="margin-bottom: 1rem;">🔧 Actions</h3>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Refresh", key="refresh_logs", use_container_width=True):
            st.rerun()

    with col2:
        # Export logs
        if logs:
            import json
            logs_export = []
            for log in logs:
                timestamp = get_attr(log, 'timestamp', None)
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.isoformat()
                level = str(get_attr(log, 'level', 'info'))
                if level.lower().startswith("loglevel."):
                    level = level.split(".")[-1]
                logs_export.append({
                    "timestamp": timestamp,
                    "level": level,
                    "component": get_attr(log, 'component', ''),
                    "message": get_attr(log, 'message', '')
                })

            st.download_button(
                label="📥 Export Logs",
                data=json.dumps(logs_export, indent=2),
                file_name=f"contentorbit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    with col3:
        if st.button("🧹 Clear Old Logs (7+ days)", key="clear_old_logs", use_container_width=True):
            cleared = db.clear_old_logs(days=7)
            st.success(f"Cleared {cleared} old log entries!")
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # AUTO REFRESH
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("<br>", unsafe_allow_html=True)

    auto_refresh = st.checkbox("🔴 Auto-refresh (every 10 seconds)", key="auto_refresh_logs")

    if auto_refresh:
        st.markdown("""
        <div style="
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        ">
            <span style="
                width: 8px;
                height: 8px;
                background: #ef4444;
                border-radius: 50%;
                animation: pulse 1s infinite;
            "></span>
            <span style="color: #f87171; font-size: 0.875rem;">Auto-refresh enabled - Updating every 10 seconds</span>
        </div>
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.3; }
            }
        </style>
        """, unsafe_allow_html=True)
        
        import time
        time.sleep(10)
        st.rerun()
