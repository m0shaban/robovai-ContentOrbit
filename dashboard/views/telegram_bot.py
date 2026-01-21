"""ContentOrbit Enterprise - Telegram Bot Settings View

Dashboard page for chatbot/admin UI settings stored in SQLite.
"""

import os
from pathlib import Path

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

    st.markdown("### ✅ System status")

    def _mask(v: str, keep: int = 6) -> str:
        v = (v or "").strip()
        if not v:
            return "(missing)"
        if len(v) <= keep * 2:
            return "***"
        return f"{v[:keep]}…{v[-keep:]}"

    # Telegram config (from config manager; hydrated from env if missing)
    try:
        tg_cfg = getattr(config.app_config, "telegram", None)
        tg_token = (getattr(tg_cfg, "bot_token", "") or "").strip()
        tg_channel = (getattr(tg_cfg, "channel_id", "") or "").strip()
        tg_admins = getattr(tg_cfg, "admin_user_ids", []) or []
    except Exception:
        tg_token, tg_channel, tg_admins = "", "", []

    chatbot_enabled = (
        os.getenv("ENABLE_TELEGRAM_CHATBOT", "1") or "1"
    ).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    lock_path = (os.getenv("TG_POLL_LOCK_PATH") or "/tmp/telegram_polling.lock").strip()
    lock_stale = (os.getenv("TG_POLL_LOCK_STALE_SECONDS") or "600").strip()
    lock_wait = (os.getenv("TG_POLL_LOCK_MAX_WAIT_SECONDS") or "120").strip()

    bg_dir = Path((os.getenv("LOCAL_BACKGROUNDS_DIR") or "assets/backgrounds").strip())
    try:
        bg_count = len([p for p in bg_dir.glob("*") if p.is_file()])
    except Exception:
        bg_count = 0

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Bot token", "OK" if tg_token else "Missing")
    s2.metric("Channel", "OK" if tg_channel else "Missing")
    s3.metric("Admins", str(len(tg_admins)))
    s4.metric("Chatbot polling", "ON" if chatbot_enabled else "OFF")

    with st.expander("Details", expanded=False):
        st.write("**Telegram**")
        st.code(
            "\n".join(
                [
                    f"TELEGRAM_TOKEN={_mask(os.getenv('TELEGRAM_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN') or tg_token)}",
                    f"CHANNEL_ID={(os.getenv('CHANNEL_ID') or os.getenv('TELEGRAM_CHANNEL_ID') or tg_channel or '(missing)')}",
                    f"ADMIN_USER_ID={(os.getenv('ADMIN_USER_ID') or '(missing)')}",
                ]
            ),
            language="text",
        )

        st.write("**Polling lock**")
        st.code(
            "\n".join(
                [
                    f"ENABLE_TELEGRAM_CHATBOT={'1' if chatbot_enabled else '0'}",
                    f"TG_POLL_LOCK_PATH={lock_path}",
                    f"TG_POLL_LOCK_STALE_SECONDS={lock_stale}",
                    f"TG_POLL_LOCK_MAX_WAIT_SECONDS={lock_wait}",
                ]
            ),
            language="text",
        )

        st.write("**Images / branding**")
        st.code(
            "\n".join(
                [
                    f"LOCAL_BACKGROUNDS_DIR={str(bg_dir)} (files: {bg_count})",
                    f"ENABLE_IMAGE_AI={(os.getenv('ENABLE_IMAGE_AI') or '0')}",
                    f"IMAGE_WATERMARK_TEXT={(os.getenv('IMAGE_WATERMARK_TEXT') or '').strip()}",
                    f"AUTO_EMOJI_TITLE={(os.getenv('AUTO_EMOJI_TITLE') or '1')}",
                ]
            ),
            language="text",
        )

    st.markdown("### 📋 Render quick defaults (non-secret)")
    st.caption("Copy/paste these into Render. Secrets stay in the main env template.")
    st.code(
        "\n".join(
            [
                "ENABLE_TELEGRAM_CHATBOT=1",
                "TG_POLL_LOCK_PATH=/tmp/telegram_polling.lock",
                "TG_POLL_LOCK_STALE_SECONDS=600",
                "TG_POLL_LOCK_MAX_WAIT_SECONDS=120",
                "ENABLE_IMAGE_AI=0",
                "LOCAL_BACKGROUNDS_ENABLED=1",
                "LOCAL_BACKGROUNDS_DIR=assets/backgrounds",
                "LOCAL_BACKGROUNDS_STRATEGY=topic",
                "LOCAL_BACKGROUNDS_DIM=0.12",
                "LOCAL_BACKGROUNDS_BLUR=0",
                "IMAGE_WATERMARK_ENABLED=1",
                "AUTO_EMOJI_TITLE=1",
            ]
        ),
        language="text",
    )

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

    filter_q = st.text_input("Filter by chat_id", value="").strip()
    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        bulk_enabled = st.selectbox(
            "Bulk enabled", options=["(no change)", "Enable", "Disable"], index=0
        )
    with col_b:
        bulk_auto = st.selectbox(
            "Bulk auto reply", options=["(no change)", "On", "Off"], index=0
        )
    with col_c:
        bulk_cta = st.selectbox(
            "Bulk CTA", options=["(no change)", "On", "Off"], index=0
        )

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

    if filter_q:
        rows = [r for r in rows if filter_q in str(r.get("chat_id", ""))]

    if rows and any(x != "(no change)" for x in (bulk_enabled, bulk_auto, bulk_cta)):
        if st.button("Apply bulk changes to filtered groups", use_container_width=True):
            for r in rows:
                chat_id = r["chat_id"]
                enabled = bool(r["enabled"])
                auto_reply = bool(r["auto_reply"])
                cta_enabled = bool(r["cta_enabled"])

                if bulk_enabled == "Enable":
                    enabled = True
                elif bulk_enabled == "Disable":
                    enabled = False

                if bulk_auto == "On":
                    auto_reply = True
                elif bulk_auto == "Off":
                    auto_reply = False

                if bulk_cta == "On":
                    cta_enabled = True
                elif bulk_cta == "Off":
                    cta_enabled = False

                db.update_group_settings(
                    chat_id,
                    enabled=enabled,
                    auto_reply=auto_reply,
                    cta_enabled=cta_enabled,
                    language=(r["language"] or "ar"),
                )
            st.success("✅ Bulk changes applied")

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
