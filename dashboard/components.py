"""
ContentOrbit Enterprise - Dashboard Components
==============================================
Premium reusable UI components with modern design.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List


def render_header():
    """Render the main header with gradient branding"""
    st.markdown(
        """
    <div style="text-align: center; padding: 1.5rem 0;">
        <h1 style="
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            font-weight: 800;
        ">🚀 ContentOrbit Enterprise</h1>
        <p style="color: #a5b4fc; font-size: 1.1rem;">Your Content, Everywhere</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar_nav():
    """Render sidebar navigation - kept for backwards compatibility"""
    pass


def render_metric_card(
    title: str, value: Any, delta: Optional[str] = None, icon: str = "📊"
):
    """Render a premium styled metric card"""
    delta_html = (
        f'<p style="color: #10b981; font-size: 0.875rem; margin: 0;">{delta}</p>'
        if delta
        else ""
    )

    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(236, 72, 153, 0.3) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        transition: all 0.3s ease;
    ">
        <p style="font-size: 0.875rem; margin: 0; color: #a5b4fc;">{icon} {title}</p>
        <h2 style="font-size: 2.5rem; margin: 0.5rem 0; color: white; font-weight: 700;">{value}</h2>
        {delta_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_status_badge(is_running: bool):
    """Render system status badge with animation"""
    if is_running:
        st.markdown(
            """
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(16, 185, 129, 0.2);
            border: 2px solid #10b981;
            color: #10b981;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
        ">
            <span style="
                width: 10px;
                height: 10px;
                background: #10b981;
                border-radius: 50%;
                animation: pulse 2s infinite;
            "></span>
            Running
        </div>
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.5; transform: scale(1.2); }
            }
        </style>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(239, 68, 68, 0.2);
            border: 2px solid #ef4444;
            color: #ef4444;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
        ">
            <span style="
                width: 10px;
                height: 10px;
                background: #ef4444;
                border-radius: 50%;
            "></span>
            Stopped
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_platform_status(platforms: Dict[str, bool]):
    """Render platform configuration status cards"""
    cols = st.columns(len(platforms))

    for col, (platform, is_configured) in zip(cols, platforms.items()):
        with col:
            icon = "✅" if is_configured else "❌"
            border_color = "#10b981" if is_configured else "#ef4444"
            bg_color = (
                "rgba(16, 185, 129, 0.1)" if is_configured else "rgba(239, 68, 68, 0.1)"
            )

            st.markdown(
                f"""
            <div style="
                text-align: center;
                padding: 1.25rem;
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 16px;
                transition: all 0.3s ease;
            ">
                <span style="font-size: 1.5rem;">{icon}</span>
                <p style="margin: 0.5rem 0 0 0; color: white; font-weight: 600;">
                    {platform}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_log_entry(log):
    """Render a single log entry - handles both dict and Pydantic model"""
    # Handle both dict and Pydantic model
    if hasattr(log, "level"):
        level = str(log.level).lower()
        timestamp = log.timestamp
        component = getattr(log, "component", "system")
        action = getattr(log, "action", "")
        message = getattr(log, "message", "")
    else:
        level = str(log.get("level", "info")).lower()
        timestamp = log.get("timestamp", "")
        component = log.get("component", "system")
        action = log.get("action", "")
        message = log.get("message", "")

    # Remove 'loglevel.' prefix if present
    if level.startswith("loglevel."):
        level = level.replace("loglevel.", "")

    level_styles = {
        "debug": {"color": "#64748b", "bg": "rgba(100, 116, 139, 0.1)", "icon": "🔍"},
        "info": {"color": "#6366f1", "bg": "rgba(99, 102, 241, 0.1)", "icon": "ℹ️"},
        "warning": {"color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.1)", "icon": "⚠️"},
        "error": {"color": "#ef4444", "bg": "rgba(239, 68, 68, 0.1)", "icon": "❌"},
        "critical": {"color": "#dc2626", "bg": "rgba(220, 38, 38, 0.1)", "icon": "🚨"},
        "success": {"color": "#10b981", "bg": "rgba(16, 185, 129, 0.1)", "icon": "✅"},
    }

    style = level_styles.get(level, level_styles["info"])

    if isinstance(timestamp, datetime):
        timestamp_str = timestamp.strftime("%H:%M:%S")
    elif timestamp:
        timestamp_str = str(timestamp)[:8]
    else:
        timestamp_str = "--:--:--"

    st.markdown(
        f"""
    <div style="
        background: {style['bg']};
        border-left: 4px solid {style['color']};
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.25rem;">{style['icon']}</span>
                <span style="
                    background: {style['color']}30;
                    color: {style['color']};
                    padding: 0.25rem 0.75rem;
                    border-radius: 8px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                ">{level}</span>
                <span style="color: #a5b4fc; font-weight: 500;">[{component}]</span>
                {f'<span style="color: #64748b;">{action}</span>' if action else ''}
            </div>
            <span style="color: #64748b; font-size: 0.75rem; font-family: monospace;">{timestamp_str}</span>
        </div>
        <p style="margin: 0.75rem 0 0 0; color: #e2e8f0; font-size: 0.9rem;">{message}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_feed_card(feed):
    """Render an RSS feed card - handles both dict and Pydantic model"""
    # Handle both dict and Pydantic model
    if hasattr(feed, "name"):
        name = feed.name
        url = getattr(feed, "url", "")
        category = str(getattr(feed, "category", "other"))
        enabled = getattr(feed, "enabled", True)
        feed_id = getattr(feed, "id", "")
    else:
        name = feed.get("name", "Unknown")
        url = feed.get("url", "")
        category = feed.get("category", "other")
        enabled = feed.get("enabled", True)
        feed_id = feed.get("id", "")

    border_color = "#10b981" if enabled else "#64748b"
    status_text = "Active" if enabled else "Disabled"
    status_icon = "✅" if enabled else "⏸️"

    st.markdown(
        f"""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 0.5rem;">
            <div style="flex: 1; min-width: 200px;">
                <h4 style="margin: 0; color: white; font-weight: 600;">{name}</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0.25rem 0; word-break: break-all;">
                    {url[:50]}{'...' if len(url) > 50 else ''}
                </p>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="
                    background: rgba(99, 102, 241, 0.2);
                    color: #a5b4fc;
                    padding: 0.25rem 0.75rem;
                    border-radius: 8px;
                    font-size: 0.75rem;
                    font-weight: 500;
                ">{category}</span>
                <span style="
                    background: {border_color}20;
                    color: {border_color};
                    padding: 0.25rem 0.75rem;
                    border-radius: 8px;
                    font-size: 0.75rem;
                    font-weight: 500;
                ">{status_icon} {status_text}</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def format_time_ago(dt) -> str:
    """Format datetime as human-readable time ago"""
    if dt is None:
        return "Never"

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except:
            return dt

    if not isinstance(dt, datetime):
        return str(dt)

    now = datetime.utcnow()

    # Handle timezone-aware datetime
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    diff = now - dt

    if diff.days > 30:
        return dt.strftime("%b %d, %Y")
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"


def render_empty_state(
    icon: str,
    title: str,
    description: str,
    action_text: str = None,
    action_key: str = None,
):
    """Render an empty state placeholder"""
    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
        border: 2px dashed rgba(99, 102, 241, 0.5);
        border-radius: 16px;
        padding: 3rem;
        text-align: center;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="color: white; margin-bottom: 0.5rem;">{title}</h3>
        <p style="color: #a5b4fc; margin: 0;">{description}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if action_text and action_key:
        st.button(action_text, key=action_key, use_container_width=True, type="primary")


def render_progress_bar(value: float, label: str = ""):
    """Render a styled progress bar"""
    percentage = min(max(value * 100, 0), 100)

    color = (
        "#10b981" if percentage < 80 else "#f59e0b" if percentage < 100 else "#ef4444"
    )

    st.markdown(
        f"""
    <div style="margin: 1rem 0;">
        {f'<p style="color: #a5b4fc; margin-bottom: 0.5rem; font-size: 0.875rem;">{label}</p>' if label else ''}
        <div style="
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            height: 12px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, {color} 0%, {color}80 100%);
                height: 100%;
                width: {percentage}%;
                border-radius: 8px;
                transition: width 0.5s ease;
            "></div>
        </div>
        <p style="color: #64748b; font-size: 0.75rem; margin-top: 0.25rem; text-align: right;">
            {percentage:.0f}%
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_stat_card(
    icon: str, label: str, value: Any, trend: str = None, trend_positive: bool = True
):
    """Render a compact stat card"""
    trend_html = ""
    if trend:
        trend_color = "#10b981" if trend_positive else "#ef4444"
        trend_icon = "↑" if trend_positive else "↓"
        trend_html = f'<span style="color: {trend_color}; font-size: 0.75rem;">{trend_icon} {trend}</span>'

    st.markdown(
        f"""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    ">
        <div style="
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(236, 72, 153, 0.3) 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        ">{icon}</div>
        <div style="flex: 1;">
            <p style="color: #64748b; font-size: 0.75rem; margin: 0;">{label}</p>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: white; font-size: 1.5rem; font-weight: 700;">{value}</span>
                {trend_html}
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
