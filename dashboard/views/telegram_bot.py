"""ContentOrbit Enterprise - Telegram Bot Settings View

Dashboard page for chatbot/admin UI settings stored in SQLite.
"""

import streamlit as st


def render_telegram_bot_page(config, db):
    st.markdown(
        """
        <div style="text-align:center; padding: 1.5rem 0;">
            <h1 style="margin:0;">🤖 Telegram Bot</h1>
            <p style="color:#a5b4fc; margin-top:0.5rem;">Chatbot + Admin controls</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## ⚙️ Chatbot Settings")

    col1, col2 = st.columns(2)

    with col1:
        daily = db.get_setting("daily_free_questions", "5")
        daily_limit = st.number_input(
            "Daily free technical questions / user",
            min_value=0,
            max_value=100,
            value=int(daily) if str(daily).isdigit() else 5,
            step=1,
        )

    with col2:
        contact = db.get_setting("contact_username", "@mohamedshabanai")
        contact_username = st.text_input("Business contact username", value=contact)

    if st.button("💾 Save Chatbot Settings", use_container_width=True):
        db.set_setting("daily_free_questions", str(daily_limit))
        db.set_setting(
            "contact_username", contact_username.strip() or "@mohamedshabanai"
        )
        st.success("✅ Saved!")

    st.markdown("---")
    st.markdown("## 👥 Group Settings")

    st.caption(
        "This reads from the `group_settings` table (created when commands are used inside groups)."
    )

    try:
        with db._get_cursor() as cursor:  # internal helper; OK for dashboard
            cursor.execute(
                "SELECT chat_id, enabled, auto_reply, cta_enabled, language, updated_at FROM group_settings ORDER BY updated_at DESC LIMIT 200"
            )
            rows = cursor.fetchall()
    except Exception:
        rows = []

    if not rows:
        st.info(
            "No groups recorded yet. Use /group_on inside a group to create an entry."
        )
        return

    for row in rows:
        chat_id = row["chat_id"]
        with st.expander(f"Group: {chat_id}"):
            enabled = st.checkbox(
                "Enabled", value=bool(row["enabled"]), key=f"g_enabled_{chat_id}"
            )
            auto_reply = st.checkbox(
                "Auto reply", value=bool(row["auto_reply"]), key=f"g_auto_{chat_id}"
            )
            cta_enabled = st.checkbox(
                "CTA enabled", value=bool(row["cta_enabled"]), key=f"g_cta_{chat_id}"
            )
            language = st.selectbox(
                "Language",
                options=["ar", "en"],
                index=0 if (row["language"] or "ar") == "ar" else 1,
                key=f"g_lang_{chat_id}",
            )

            if st.button("Save group", key=f"save_group_{chat_id}"):
                db.update_group_settings(
                    chat_id,
                    enabled=enabled,
                    auto_reply=auto_reply,
                    cta_enabled=cta_enabled,
                    language=language,
                )
                st.success("Saved")
