"""
ContentOrbit Enterprise - Sources Management Page
==================================================
Premium RSS feeds and content sources management.
"""

import streamlit as st
from datetime import datetime
import uuid

from core.models import RSSFeed


def render_sources_page(config, db):
    """Render the RSS feeds management page"""

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        ">📡 Content Sources</h1>
        <p style="color: #a5b4fc; font-size: 1.1rem;">
            Manage your RSS feeds and content sources
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Helper to get feed attribute
    def get_attr(feed, attr, default=None):
        if hasattr(feed, attr):
            return getattr(feed, attr, default)
        return feed.get(attr, default) if isinstance(feed, dict) else default

    # Get feeds from config
    feeds = config.feeds or []
    active_feeds = [f for f in feeds if get_attr(f, 'enabled', True)]
    disabled_feeds = [f for f in feeds if not get_attr(f, 'enabled', True)]
    categories = set(get_attr(f, 'category', 'general') for f in feeds)

    # ═══════════════════════════════════════════════════════════════════════════
    # STATS CARDS
    # ═══════════════════════════════════════════════════════════════════════════

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        ">
            <p style="color: #a5b4fc; margin: 0; font-size: 0.875rem;">📡 Total Feeds</p>
            <p style="color: #6366f1; font-size: 2.5rem; font-weight: 700; margin: 0.25rem 0;">{len(feeds)}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        ">
            <p style="color: #34d399; margin: 0; font-size: 0.875rem;">✅ Active</p>
            <p style="color: #10b981; font-size: 2.5rem; font-weight: 700; margin: 0.25rem 0;">{len(active_feeds)}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        ">
            <p style="color: #fbbf24; margin: 0; font-size: 0.875rem;">⏸️ Disabled</p>
            <p style="color: #f59e0b; font-size: 2.5rem; font-weight: 700; margin: 0.25rem 0;">{len(disabled_feeds)}</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="
            background: rgba(236, 72, 153, 0.1);
            border: 1px solid rgba(236, 72, 153, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        ">
            <p style="color: #f472b6; margin: 0; font-size: 0.875rem;">🏷️ Categories</p>
            <p style="color: #ec4899; font-size: 2.5rem; font-weight: 700; margin: 0.25rem 0;">{len(categories)}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # ADD NEW FEED - In Sidebar
    # ═══════════════════════════════════════════════════════════════════════════

    with st.sidebar:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        ">
            <h3 style="color: white; margin: 0 0 0.5rem 0;">➕ Add New Feed</h3>
            <p style="color: #a5b4fc; font-size: 0.875rem; margin: 0;">Add RSS/Atom feeds as content sources</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("add_feed_form"):
            feed_name = st.text_input("Feed Name", placeholder="Tech News Daily")
            feed_url = st.text_input("Feed URL", placeholder="https://example.com/rss.xml")
            
            feed_category = st.selectbox(
                "Category",
                options=["tech", "business", "science", "health", "entertainment", "general"],
            )
            
            feed_language = st.selectbox(
                "Language",
                options=["en", "ar", "es", "fr", "de"],
                index=0
            )
            
            feed_enabled = st.checkbox("Enabled", value=True)

            if st.form_submit_button("➕ Add Feed", use_container_width=True, type="primary"):
                if feed_name and feed_url:
                    new_feed = RSSFeed(
                        id=str(uuid.uuid4())[:8],
                        name=feed_name,
                        url=feed_url,
                        category=feed_category,
                        language=feed_language,
                        enabled=feed_enabled,
                    )
                    config.add_feed(new_feed)
                    st.success(f"✅ Feed '{feed_name}' added!")
                    st.rerun()
                else:
                    st.error("Please fill in Name and URL!")

    # ═══════════════════════════════════════════════════════════════════════════
    # FILTER & SEARCH
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h4 style="margin: 0 0 1rem 0; color: #a5b4fc;">🔍 Filter Feeds</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        search_query = st.text_input("🔍 Search", placeholder="Search by name or URL...")

    with col2:
        filter_category = st.selectbox(
            "Category",
            options=["All"] + sorted(list(categories)),
            key="filter_category"
        )

    with col3:
        filter_status = st.selectbox(
            "Status",
            options=["All", "Active", "Disabled"],
            key="filter_status"
        )

    # Apply filters
    filtered_feeds = feeds

    if search_query:
        filtered_feeds = [
            f for f in filtered_feeds
            if search_query.lower() in get_attr(f, 'name', '').lower()
            or search_query.lower() in get_attr(f, 'url', '').lower()
        ]

    if filter_category != "All":
        filtered_feeds = [f for f in filtered_feeds if get_attr(f, 'category') == filter_category]

    if filter_status == "Active":
        filtered_feeds = [f for f in filtered_feeds if get_attr(f, 'enabled', True)]
    elif filter_status == "Disabled":
        filtered_feeds = [f for f in filtered_feeds if not get_attr(f, 'enabled', True)]

    # ═══════════════════════════════════════════════════════════════════════════
    # FEEDS LIST
    # ═══════════════════════════════════════════════════════════════════════════

    if not filtered_feeds:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 2px dashed rgba(99, 102, 241, 0.5);
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
            <h3 style="color: white; margin-bottom: 0.5rem;">No Feeds Found</h3>
            <p style="color: #a5b4fc;">Add your first RSS feed from the sidebar!</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"""
    <h3 style="margin-bottom: 1rem;">
        📋 Feeds <span style="color: #6366f1;">({len(filtered_feeds)})</span>
    </h3>
    """, unsafe_allow_html=True)

    for feed in filtered_feeds:
        feed_id = get_attr(feed, 'id', str(uuid.uuid4())[:8])
        feed_name = get_attr(feed, 'name', 'Unnamed Feed')
        feed_url = get_attr(feed, 'url', '')
        feed_category = get_attr(feed, 'category', 'general')
        feed_language = get_attr(feed, 'language', 'en')
        feed_enabled = get_attr(feed, 'enabled', True)
        last_fetched = get_attr(feed, 'last_fetched', None)

        # Status indicator
        status_color = "#10b981" if feed_enabled else "#64748b"
        status_icon = "✅" if feed_enabled else "⏸️"

        # Category colors
        category_colors = {
            "tech": "#6366f1",
            "business": "#10b981",
            "science": "#8b5cf6",
            "health": "#ef4444",
            "entertainment": "#ec4899",
            "general": "#64748b"
        }
        cat_color = category_colors.get(feed_category, "#64748b")

        with st.expander(f"{status_icon} {feed_name}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                <div style="
                    background: rgba(255, 255, 255, 0.03);
                    border-radius: 12px;
                    padding: 1rem;
                ">
                    <p style="color: #94a3b8; margin: 0.5rem 0;">
                        <strong style="color: #e2e8f0;">🔗 URL:</strong> 
                        <code style="
                            background: rgba(99, 102, 241, 0.2);
                            padding: 0.25rem 0.5rem;
                            border-radius: 4px;
                            font-size: 0.875rem;
                        ">{feed_url[:60]}{'...' if len(feed_url) > 60 else ''}</code>
                    </p>
                    <p style="color: #94a3b8; margin: 0.5rem 0;">
                        <strong style="color: #e2e8f0;">🏷️ Category:</strong> 
                        <span style="
                            background: {cat_color}33;
                            color: {cat_color};
                            padding: 0.25rem 0.75rem;
                            border-radius: 20px;
                            font-size: 0.875rem;
                        ">{feed_category}</span>
                    </p>
                    <p style="color: #94a3b8; margin: 0.5rem 0;">
                        <strong style="color: #e2e8f0;">🌐 Language:</strong> {feed_language.upper()}
                    </p>
                    <p style="color: #94a3b8; margin: 0.5rem 0;">
                        <strong style="color: #e2e8f0;">🆔 ID:</strong> <code>{feed_id}</code>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if last_fetched:
                    if isinstance(last_fetched, datetime):
                        last_fetched_str = last_fetched.strftime("%Y-%m-%d %H:%M")
                    else:
                        last_fetched_str = str(last_fetched)
                    st.markdown(f"**⏰ Last Fetched:** {last_fetched_str}")

            with col2:
                st.markdown("""
                <p style="color: #a5b4fc; font-weight: 600; margin-bottom: 0.75rem;">⚡ Actions</p>
                """, unsafe_allow_html=True)

                # Toggle status
                if feed_enabled:
                    if st.button("⏸️ Disable", key=f"disable_{feed_id}", use_container_width=True):
                        config.update_feed(feed_id, enabled=False)
                        st.success(f"Feed disabled!")
                        st.rerun()
                else:
                    if st.button("▶️ Enable", key=f"enable_{feed_id}", use_container_width=True):
                        config.update_feed(feed_id, enabled=True)
                        st.success(f"Feed enabled!")
                        st.rerun()

                # Fetch now
                if st.button("🔄 Fetch", key=f"fetch_{feed_id}", use_container_width=True):
                    with st.spinner("Fetching..."):
                        try:
                            from core.rss_parser import RSSParser
                            parser = RSSParser()
                            result = parser.fetch_feed(feed_url)
                            entries = result.get('entries', []) if isinstance(result, dict) else []
                            st.success(f"Fetched {len(entries)} articles!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

                # Delete
                if st.button("🗑️ Delete", key=f"delete_{feed_id}", use_container_width=True, type="secondary"):
                    config.delete_feed(feed_id)
                    st.success(f"Feed deleted!")
                    st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # BULK ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    ">
        <h4 style="margin: 0 0 0.5rem 0; color: #a5b4fc;">🔧 Bulk Actions</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("▶️ Enable All", key="enable_all_feeds", use_container_width=True):
            for feed in feeds:
                feed_id = get_attr(feed, 'id')
                if feed_id:
                    config.update_feed(feed_id, enabled=True)
            st.success("All feeds enabled!")
            st.rerun()

    with col2:
        if st.button("⏸️ Disable All", key="disable_all_feeds", use_container_width=True):
            for feed in feeds:
                feed_id = get_attr(feed, 'id')
                if feed_id:
                    config.update_feed(feed_id, enabled=False)
            st.success("All feeds disabled!")
            st.rerun()

    with col3:
        if st.button("🔄 Fetch All Active", key="fetch_all_feeds", use_container_width=True):
            with st.spinner("Fetching all active feeds..."):
                from core.rss_parser import RSSParser
                parser = RSSParser()
                success_count = 0
                error_count = 0

                for feed in active_feeds:
                    try:
                        url = get_attr(feed, 'url')
                        if url:
                            parser.fetch_feed(url)
                            success_count += 1
                    except Exception:
                        error_count += 1

                st.success(f"Fetched {success_count} feeds. {error_count} errors.")

    # ═══════════════════════════════════════════════════════════════════════════
    # IMPORT/EXPORT
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    ">
        <h4 style="margin: 0 0 0.5rem 0; color: #a5b4fc;">📦 Import / Export</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if feeds:
            import json
            feeds_export = []
            for f in feeds:
                feeds_export.append({
                    "id": get_attr(f, 'id'),
                    "name": get_attr(f, 'name'),
                    "url": get_attr(f, 'url'),
                    "category": get_attr(f, 'category'),
                    "language": get_attr(f, 'language'),
                    "enabled": get_attr(f, 'enabled', True)
                })

            st.download_button(
                label="📥 Export Feeds (JSON)",
                data=json.dumps(feeds_export, indent=2),
                file_name=f"contentorbit_feeds_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

    with col2:
        uploaded_file = st.file_uploader(
            "📤 Import Feeds (JSON)",
            type=["json"],
            key="import_feeds"
        )

        if uploaded_file is not None:
            try:
                import json
                imported_feeds = json.load(uploaded_file)

                if st.button("⬆️ Import", key="do_import", use_container_width=True):
                    imported_count = 0
                    for feed_data in imported_feeds:
                        new_feed = RSSFeed(
                            id=feed_data.get("id", str(uuid.uuid4())[:8]),
                            name=feed_data.get("name", "Imported Feed"),
                            url=feed_data.get("url", ""),
                            category=feed_data.get("category", "general"),
                            language=feed_data.get("language", "en"),
                            enabled=feed_data.get("enabled", True),
                        )
                        config.add_feed(new_feed)
                        imported_count += 1

                    st.success(f"Imported {imported_count} feeds!")
                    st.rerun()

            except Exception as e:
                st.error(f"Error importing feeds: {str(e)}")

    # ═══════════════════════════════════════════════════════════════════════════
    # OPML IMPORT
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("📜 Import OPML (from other RSS readers)"):
        opml_file = st.file_uploader(
            "Upload OPML file",
            type=["opml", "xml"],
            key="opml_import"
        )

        if opml_file is not None:
            try:
                import xml.etree.ElementTree as ET
                content = opml_file.read().decode("utf-8")
                root = ET.fromstring(content)

                outlines = root.findall(".//outline[@xmlUrl]")
                st.info(f"Found {len(outlines)} feeds in OPML file")

                if st.button("⬆️ Import OPML", key="do_opml_import", use_container_width=True):
                    imported_count = 0
                    for outline in outlines:
                        new_feed = RSSFeed(
                            id=str(uuid.uuid4())[:8],
                            name=outline.get("title") or outline.get("text") or "Imported",
                            url=outline.get("xmlUrl"),
                            category=outline.get("category", "general"),
                            language="en",
                            enabled=True,
                        )
                        config.add_feed(new_feed)
                        imported_count += 1

                    st.success(f"Imported {imported_count} feeds from OPML!")
                    st.rerun()

            except Exception as e:
                st.error(f"Error parsing OPML: {str(e)}")

    # ═══════════════════════════════════════════════════════════════════════════
    # POPULAR FEEDS SUGGESTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("💡 Suggested Tech RSS Feeds"):
        st.markdown("""
        <div style="
            background: rgba(99, 102, 241, 0.05);
            border-radius: 12px;
            padding: 1rem;
        ">
            <p style="color: #e2e8f0; margin: 0.5rem 0;"><strong>🔗 TechCrunch:</strong> <code>https://techcrunch.com/feed/</code></p>
            <p style="color: #e2e8f0; margin: 0.5rem 0;"><strong>🔗 The Verge:</strong> <code>https://www.theverge.com/rss/index.xml</code></p>
            <p style="color: #e2e8f0; margin: 0.5rem 0;"><strong>🔗 Hacker News:</strong> <code>https://hnrss.org/frontpage</code></p>
            <p style="color: #e2e8f0; margin: 0.5rem 0;"><strong>🔗 Dev.to:</strong> <code>https://dev.to/feed</code></p>
            <p style="color: #e2e8f0; margin: 0.5rem 0;"><strong>🔗 Ars Technica:</strong> <code>http://feeds.arstechnica.com/arstechnica/index</code></p>
            <p style="color: #e2e8f0; margin: 0.5rem 0;"><strong>🔗 Wired:</strong> <code>https://www.wired.com/feed/rss</code></p>
        </div>
        """, unsafe_allow_html=True)
