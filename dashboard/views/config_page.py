"""
ContentOrbit Enterprise - Configuration Page
=============================================
Premium API keys, prompts, and system settings management.
"""

import streamlit as st
from datetime import datetime


def render_config_page(config, db):
    """Render the configuration page"""

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        ">⚙️ Configuration</h1>
        <p style="color: #a5b4fc; font-size: 1.1rem;">
            Manage API keys, prompts, and system settings
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Helper to safely get nested config values
    def safe_get(obj, attr, default=""):
        if obj is None:
            return default
        val = getattr(obj, attr, default)
        return val if val is not None else default

    # ═══════════════════════════════════════════════════════════════════════════
    # TABS
    # ═══════════════════════════════════════════════════════════════════════════

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔑 API Keys", 
        "📝 Prompts", 
        "⏰ Schedule", 
        "🌐 Platforms", 
        "🎨 Branding"
    ])

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 1: API KEYS
    # ═══════════════════════════════════════════════════════════════════════════

    with tab1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        ">
            <h3 style="margin: 0 0 0.5rem 0; color: white;">🔑 API Keys & Tokens</h3>
            <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                Configure your platform API keys. Keep these secure and never share them.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # GROQ
        with st.expander("🤖 Groq AI (Required)", expanded=True):
            st.markdown("""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                border-left: 4px solid #6366f1;
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                border-radius: 0 8px 8px 0;
            ">
                <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                    🔗 Get your free API key from <a href="https://console.groq.com/keys" target="_blank" style="color: #6366f1;">console.groq.com/keys</a>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            groq_config = config.app_config.groq
            
            groq_key = st.text_input(
                "Groq API Key",
                value=safe_get(groq_config, "api_key"),
                type="password",
                help="Get your API key from console.groq.com",
            )

            current_model = safe_get(groq_config, "model", "llama-3.1-70b-versatile")
            models = [
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
                "llama-3.3-70b-versatile",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
            ]
            model_index = models.index(current_model) if current_model in models else 0
            
            groq_model = st.selectbox(
                "Model",
                options=models,
                index=model_index,
            )

            if st.button("💾 Save Groq Settings", key="save_groq", use_container_width=True):
                config.update_groq_config(api_key=groq_key, model=groq_model)
                st.success("✅ Groq settings saved!")

        # TELEGRAM
        with st.expander("📱 Telegram Bot"):
            st.markdown("""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                border-left: 4px solid #6366f1;
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                border-radius: 0 8px 8px 0;
            ">
                <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                    🔗 Create a bot with <a href="https://t.me/botfather" target="_blank" style="color: #6366f1;">@BotFather</a> on Telegram
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            tg_config = config.app_config.telegram
            
            tg_token = st.text_input(
                "Bot Token",
                value=safe_get(tg_config, "bot_token"),
                type="password",
                help="Get from @BotFather on Telegram",
            )

            tg_channel = st.text_input(
                "Channel ID",
                value=safe_get(tg_config, "channel_id"),
                help="Channel ID starting with @ or -100...",
            )

            if st.button("💾 Save Telegram Settings", key="save_telegram", use_container_width=True):
                config.update_telegram_config(bot_token=tg_token, channel_id=tg_channel)
                st.success("✅ Telegram settings saved!")

        # BLOGGER
        with st.expander("📝 Blogger"):
            st.markdown("""
            <div style="
                background: rgba(245, 158, 11, 0.1);
                border-left: 4px solid #f59e0b;
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                border-radius: 0 8px 8px 0;
            ">
                <p style="color: #fbbf24; margin: 0; font-size: 0.9rem;">
                    ⚠️ Blogger uses OAuth2. Set up credentials from <a href="https://console.cloud.google.com" target="_blank" style="color: #f59e0b;">Google Cloud Console</a>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            blogger_config = config.app_config.blogger

            blogger_id = st.text_input(
                "Blog ID",
                value=safe_get(blogger_config, "blog_id"),
                help="Your Blogger blog ID (found in blog URL)",
            )

            blogger_client_id = st.text_input(
                "Client ID",
                value=safe_get(blogger_config, "client_id"),
                type="password",
            )

            blogger_client_secret = st.text_input(
                "Client Secret",
                value=safe_get(blogger_config, "client_secret"),
                type="password",
            )

            blogger_refresh_token = st.text_area(
                "Refresh Token",
                value=safe_get(blogger_config, "refresh_token"),
                height=80,
                help="OAuth2 refresh token",
            )

            if st.button("💾 Save Blogger Settings", key="save_blogger", use_container_width=True):
                config.update_blogger_config(
                    blog_id=blogger_id,
                    client_id=blogger_client_id,
                    client_secret=blogger_client_secret,
                    refresh_token=blogger_refresh_token,
                )
                st.success("✅ Blogger settings saved!")

        # DEV.TO
        with st.expander("💻 Dev.to"):
            st.markdown("""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                border-left: 4px solid #6366f1;
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                border-radius: 0 8px 8px 0;
            ">
                <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                    🔗 Get your API key from <a href="https://dev.to/settings/extensions" target="_blank" style="color: #6366f1;">dev.to/settings/extensions</a>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            devto_config = config.app_config.devto
            
            devto_key = st.text_input(
                "API Key",
                value=safe_get(devto_config, "api_key"),
                type="password",
                help="Get from dev.to/settings/extensions",
            )

            devto_org = st.text_input(
                "Organization (Optional)",
                value=safe_get(devto_config, "organization_id"),
            )

            if st.button("💾 Save Dev.to Settings", key="save_devto", use_container_width=True):
                config.update_devto_config(
                    api_key=devto_key, organization_id=devto_org if devto_org else None
                )
                st.success("✅ Dev.to settings saved!")

        # FACEBOOK
        with st.expander("📘 Facebook"):
            st.markdown("""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                border-left: 4px solid #6366f1;
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                border-radius: 0 8px 8px 0;
            ">
                <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                    🔗 Create a Facebook App at <a href="https://developers.facebook.com" target="_blank" style="color: #6366f1;">developers.facebook.com</a>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            fb_config = config.app_config.facebook
            
            fb_token = st.text_input(
                "Page Access Token",
                value=safe_get(fb_config, "page_access_token"),
                type="password",
                help="Long-lived page access token",
            )

            fb_page_id = st.text_input(
                "Page ID", 
                value=safe_get(fb_config, "page_id")
            )

            if st.button("💾 Save Facebook Settings", key="save_facebook", use_container_width=True):
                config.update_facebook_config(
                    page_access_token=fb_token, page_id=fb_page_id
                )
                st.success("✅ Facebook settings saved!")

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 2: PROMPTS
    # ═══════════════════════════════════════════════════════════════════════════

    with tab2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        ">
            <h3 style="margin: 0 0 0.5rem 0; color: white;">📝 AI Content Prompts</h3>
            <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                Customize how the AI generates content for each platform. Use <code style="background: rgba(99, 102, 241, 0.3); padding: 2px 6px; border-radius: 4px;">{topic}</code> and <code style="background: rgba(99, 102, 241, 0.3); padding: 2px 6px; border-radius: 4px;">{source_summary}</code> as placeholders.
            </p>
        </div>
        """, unsafe_allow_html=True)

        prompts = config.app_config.prompts
        
        # Safe defaults if prompts is None
        if prompts is None:
            from core.models import SystemPrompts
            prompts = SystemPrompts()

        blogger_prompt = st.text_area(
            "📝 Blogger Prompt (Arabic)",
            value=prompts.blogger_article_prompt,
            height=180,
            help="Use {topic} and {source_summary} as placeholders",
        )

        devto_prompt = st.text_area(
            "💻 Dev.to Prompt (English)", 
            value=prompts.devto_article_prompt, 
            height=180
        )

        telegram_prompt = st.text_area(
            "📱 Telegram Prompt", 
            value=prompts.telegram_post_prompt, 
            height=120
        )

        facebook_prompt = st.text_area(
            "📘 Facebook Prompt", 
            value=prompts.facebook_post_prompt, 
            height=120
        )

        if st.button("💾 Save All Prompts", type="primary", use_container_width=True):
            config.update_prompts(
                blogger_prompt=blogger_prompt,
                devto_prompt=devto_prompt,
                telegram_prompt=telegram_prompt,
                facebook_prompt=facebook_prompt,
            )
            st.success("✅ All prompts saved!")

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 3: SCHEDULE
    # ═══════════════════════════════════════════════════════════════════════════

    with tab3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        ">
            <h3 style="margin: 0 0 0.5rem 0; color: white;">⏰ Posting Schedule</h3>
            <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                Configure when and how often content gets published automatically.
            </p>
        </div>
        """, unsafe_allow_html=True)

        schedule = config.app_config.schedule
        
        # Safe defaults if schedule is None
        if schedule is None:
            from core.models import ScheduleConfig
            schedule = ScheduleConfig()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.03);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="color: #a5b4fc; margin: 0 0 1rem 0;">📊 Frequency</h4>
            </div>
            """, unsafe_allow_html=True)
            
            interval = st.number_input(
                "Posting Interval (minutes)",
                min_value=5,
                max_value=360,
                value=schedule.posting_interval_minutes,
                step=5,
            )

            max_posts = st.number_input(
                "Max Posts Per Day",
                min_value=1,
                max_value=50,
                value=schedule.max_posts_per_day,
            )

        with col2:
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.03);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="color: #a5b4fc; margin: 0 0 1rem 0;">🕐 Active Hours</h4>
            </div>
            """, unsafe_allow_html=True)
            
            active_start = st.number_input(
                "Start Hour (0-23)",
                min_value=0,
                max_value=23,
                value=schedule.active_hours_start,
            )

            active_end = st.number_input(
                "End Hour (0-23)",
                min_value=0,
                max_value=23,
                value=schedule.active_hours_end,
            )

        timezones = [
            "UTC",
            "Africa/Cairo",
            "Asia/Riyadh",
            "Asia/Dubai",
            "Europe/London",
            "America/New_York",
        ]
        current_tz = schedule.timezone if schedule.timezone in timezones else "UTC"
        
        timezone = st.selectbox(
            "🌍 Timezone",
            options=timezones,
            index=timezones.index(current_tz),
        )

        # Schedule summary
        st.markdown(f"""
        <div style="
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
        ">
            <p style="color: #34d399; margin: 0; font-size: 0.9rem;">
                📋 <strong>Summary:</strong> Posts every <strong>{interval} minutes</strong> between <strong>{active_start}:00</strong> and <strong>{active_end}:00</strong> ({timezone}), up to <strong>{max_posts} posts/day</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💾 Save Schedule", type="primary", key="save_schedule", use_container_width=True):
            config.update_schedule(
                interval_minutes=interval,
                max_posts_per_day=max_posts,
                active_start=active_start,
                active_end=active_end,
            )
            config.app_config.schedule.timezone = timezone
            config.save()
            st.success("✅ Schedule saved!")

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 4: PLATFORMS
    # ═══════════════════════════════════════════════════════════════════════════

    with tab4:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        ">
            <h3 style="margin: 0 0 0.5rem 0; color: white;">🌐 Platform Settings</h3>
            <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                Enable or disable publishing to each platform.
            </p>
        </div>
        """, unsafe_allow_html=True)

        schedule = config.app_config.schedule

        # Platform cards
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
            ">
                <h4 style="color: #e2e8f0; margin: 0;">📝 Blogger</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0.25rem 0 0.75rem 0;">Arabic blog articles</p>
            </div>
            """, unsafe_allow_html=True)
            blogger_enabled = st.checkbox(
                "Enable Blogger", 
                value=schedule.blogger_enabled,
                key="blogger_enabled"
            )

            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
            ">
                <h4 style="color: #e2e8f0; margin: 0;">💻 Dev.to</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0.25rem 0 0.75rem 0;">English tech articles</p>
            </div>
            """, unsafe_allow_html=True)
            devto_enabled = st.checkbox(
                "Enable Dev.to", 
                value=schedule.devto_enabled,
                key="devto_enabled"
            )

        with col2:
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
            ">
                <h4 style="color: #e2e8f0; margin: 0;">📱 Telegram</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0.25rem 0 0.75rem 0;">Channel posts & notifications</p>
            </div>
            """, unsafe_allow_html=True)
            telegram_enabled = st.checkbox(
                "Enable Telegram", 
                value=schedule.telegram_enabled,
                key="telegram_enabled"
            )

            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
            ">
                <h4 style="color: #e2e8f0; margin: 0;">📘 Facebook</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0.25rem 0 0.75rem 0;">Page posts</p>
            </div>
            """, unsafe_allow_html=True)
            facebook_enabled = st.checkbox(
                "Enable Facebook", 
                value=schedule.facebook_enabled,
                key="facebook_enabled"
            )

        if st.button("💾 Save Platform Settings", type="primary", key="save_platforms", use_container_width=True):
            config.app_config.schedule.blogger_enabled = blogger_enabled
            config.app_config.schedule.devto_enabled = devto_enabled
            config.app_config.schedule.telegram_enabled = telegram_enabled
            config.app_config.schedule.facebook_enabled = facebook_enabled
            config.save()
            st.success("✅ Platform settings saved!")

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 5: BRANDING
    # ═══════════════════════════════════════════════════════════════════════════

    with tab5:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        ">
            <h3 style="margin: 0 0 0.5rem 0; color: white;">🎨 White-Label Branding</h3>
            <p style="color: #a5b4fc; margin: 0; font-size: 0.9rem;">
                Customize the dashboard appearance with your brand.
            </p>
        </div>
        """, unsafe_allow_html=True)

        bot_name = st.text_input(
            "🏷️ Bot Name",
            value=config.app_config.brand_name,
            help="Name displayed in the dashboard header",
        )

        tagline = st.text_input(
            "💬 Tagline", 
            value=config.app_config.brand_tagline,
            help="Subtitle shown under the bot name"
        )

        # Preview
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 2rem;
            margin: 1.5rem 0;
            text-align: center;
        ">
            <p style="color: #64748b; font-size: 0.8rem; margin: 0 0 0.5rem 0;">PREVIEW</p>
            <h2 style="
                font-size: 2rem;
                background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0;
            ">{bot_name or 'ContentOrbit'}</h2>
            <p style="color: #a5b4fc; margin: 0.5rem 0 0 0;">{tagline or 'AI-Powered Content Automation'}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💾 Save Branding", type="primary", key="save_branding", use_container_width=True):
            config.app_config.brand_name = bot_name
            config.app_config.brand_tagline = tagline
            config.save()
            st.success("✅ Branding saved!")

    # ═══════════════════════════════════════════════════════════════════════════
    # EXPORT/IMPORT CONFIG
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <h3 style="margin-bottom: 1rem;">📦 Backup & Restore</h3>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Export config (without sensitive keys)
        if st.button("📥 Export Config (Safe)", key="export_config", use_container_width=True):
            import json
            export_data = {
                "brand_name": config.app_config.brand_name,
                "brand_tagline": config.app_config.brand_tagline,
                "schedule": {
                    "posting_interval_minutes": config.app_config.schedule.posting_interval_minutes,
                    "max_posts_per_day": config.app_config.schedule.max_posts_per_day,
                    "active_hours_start": config.app_config.schedule.active_hours_start,
                    "active_hours_end": config.app_config.schedule.active_hours_end,
                    "timezone": config.app_config.schedule.timezone,
                    "blogger_enabled": config.app_config.schedule.blogger_enabled,
                    "devto_enabled": config.app_config.schedule.devto_enabled,
                    "telegram_enabled": config.app_config.schedule.telegram_enabled,
                    "facebook_enabled": config.app_config.schedule.facebook_enabled,
                },
                "exported_at": datetime.now().isoformat()
            }
            
            st.download_button(
                label="💾 Download Config",
                data=json.dumps(export_data, indent=2),
                file_name=f"contentorbit_config_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

    with col2:
        st.info("💡 API keys are not exported for security. Re-enter them after importing.")

    # ═══════════════════════════════════════════════════════════════════════════
    # DANGER ZONE
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("⚠️ Danger Zone"):
        st.markdown("""
        <div style="
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <p style="color: #f87171; margin: 0; font-size: 0.9rem;">
                ⚠️ These actions cannot be undone. Use with caution.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear All Logs", key="clear_all_logs", use_container_width=True):
                db.clear_old_logs(days=0)
                st.success("All logs cleared!")
                
        with col2:
            if st.button("🔄 Reset Config to Defaults", key="reset_config", use_container_width=True):
                st.warning("This feature requires manual config reset. Edit config.yaml directly.")
