"""ContentOrbit Enterprise - Telegram Chatbot

Interactive Telegram bot UI/UX layer (admin panel + chatbot + group tools).

Runs alongside the publishing pipeline worker (main_bot.py).

Usage:
  python telegram_chatbot.py

Notes:
- Uses the same bot token as the publisher.
- Worker (main_bot.py) does NOT poll updates, so it can run in parallel.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Add project root to path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import ConfigManager
from core.database_manager import DatabaseManager
from core.content_orchestrator import ContentOrchestrator
from core.ai_engine.llm_client import LLMClient

logger = logging.getLogger("ContentOrbit.TelegramChatbot")
logging.basicConfig(level=logging.INFO)


CONTACT_USERNAME = "@mohamedshabanai"
DEFAULT_DAILY_FREE_QUESTIONS = 5


class AskState(StatesGroup):
    waiting_for_question = State()


class PromptEditState(StatesGroup):
    waiting_for_prompt_text = State()


def is_admin(config: ConfigManager, user_id: int) -> bool:
    tg = config.app_config.telegram
    return bool(tg and user_id in (tg.admin_user_ids or []))


def main_menu_kb(is_admin_user: bool):
    kb = InlineKeyboardBuilder()
    kb.button(text="🧠 اسأل سؤال تقني", callback_data="menu:ask")
    kb.button(text="💼 خدمات RoboVAI", callback_data="menu:business")
    kb.button(text="🔗 روابطنا", callback_data="menu:links")
    if is_admin_user:
        kb.button(text="🚀 نفّذ النشر الآن", callback_data="menu:run_pipeline")
        kb.button(text="⚙️ إعدادات البوت", callback_data="menu:settings")
        kb.button(text="📝 تعديل البرومبت", callback_data="menu:prompts")
        kb.button(text="👥 إعدادات الجروبات", callback_data="menu:groups")
    kb.adjust(2)
    return kb.as_markup()


def prompts_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📱 برومبت تيليجرام", callback_data="prompts:telegram")
    kb.button(text="📝 برومبت Blogger (AR)", callback_data="prompts:blogger")
    kb.button(text="💻 برومبت Dev.to (EN)", callback_data="prompts:devto")
    kb.button(text="📘 برومبت فيسبوك", callback_data="prompts:facebook")
    kb.button(text="⬅️ رجوع", callback_data="menu:settings")
    kb.adjust(2)
    return kb.as_markup()


def _get_prompt_value(config: ConfigManager, key: str) -> str:
    prompts = config.app_config.prompts
    if key == "telegram":
        return prompts.telegram_post_prompt
    if key == "blogger":
        return prompts.blogger_article_prompt
    if key == "devto":
        return prompts.devto_article_prompt
    if key == "facebook":
        return prompts.facebook_post_prompt
    return ""


def _update_prompt(config: ConfigManager, key: str, value: str) -> bool:
    if key == "telegram":
        return config.update_prompts(telegram_prompt=value)
    if key == "blogger":
        return config.update_prompts(blogger_prompt=value)
    if key == "devto":
        return config.update_prompts(devto_prompt=value)
    if key == "facebook":
        return config.update_prompts(facebook_prompt=value)
    return False


def links_text() -> str:
    return (
        "🔗 روابط RoboVAI الرسمية:\n\n"
        "📘 Facebook: https://www.facebook.com/robovaisolutions\n"
        "📱 Telegram Hub: https://t.me/robovai_hub\n"
        "📝 Blogger: https://robovai.blogspot.com\n"
        "💻 Dev.to: https://dev.to/mohamedshabanai/\n"
    )


def business_text() -> str:
    return (
        "💼 RoboVAI Solutions\n\n"
        "أقدر أعملك نظام زي ContentOrbit (وأقوى) يشمل:\n"
        "- نشر تلقائي متعدد المنصات (Blogger/Dev.to/Telegram/Facebook)\n"
        "- استراتيجية CTA ذكية (Hub & Spoke)\n"
        "- توليد صور تلقائي + دعم العربية RTL\n"
        "- Dashboard إدارة كامل + صلاحيات Admin\n"
        "- Chatbot للجروبات والرسائل الخاصة\n\n"
        f"لو حابب نسخة Business تواصل معايا مباشرة: {CONTACT_USERNAME}"
    )


async def ensure_defaults(db: DatabaseManager):
    if db.get_setting("daily_free_questions") is None:
        db.set_setting("daily_free_questions", str(DEFAULT_DAILY_FREE_QUESTIONS))


def today_key() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


async def handle_question(
    message: Message,
    config: ConfigManager,
    db: DatabaseManager,
    llm: LLMClient,
    question: str,
    language: str = "ar",
):
    daily_limit_raw = db.get_setting(
        "daily_free_questions", str(DEFAULT_DAILY_FREE_QUESTIONS)
    )
    try:
        daily_limit = int(daily_limit_raw or DEFAULT_DAILY_FREE_QUESTIONS)
    except Exception:
        daily_limit = DEFAULT_DAILY_FREE_QUESTIONS

    used = db.get_daily_questions_used(message.from_user.id, today_key())
    if used >= daily_limit:
        await message.answer(
            (
                "⛔ وصلت للحد المجاني لليوم.\n\n"
                f"لو محتاج دعم إضافي أو استشارة مدفوعة تواصل معايا: {CONTACT_USERNAME}"
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    db.increment_daily_questions(message.from_user.id, today_key(), inc=1)

    await message.answer("⏳ تمام… بحلل السؤال وبجهز الإجابة.")
    try:
        answer = await llm.answer_technical_question(question, language=language)
        await message.answer(answer)
    except Exception as e:
        logger.exception("Q&A failed")
        await message.answer(
            "حصل خطأ مؤقت في خدمة الإجابات. جرّب تاني بعد شوية أو ابعتلي على الخاص."
            f"\n{CONTACT_USERNAME}"
        )


async def build_app() -> (
    tuple[Dispatcher, Bot, ConfigManager, DatabaseManager, LLMClient]
):
    config = ConfigManager()
    config.load()

    db = DatabaseManager()
    await ensure_defaults(db)

    bot = Bot(token=config.app_config.telegram.bot_token)
    dp = Dispatcher()
    router = Router()

    llm = LLMClient(config)

    # /start
    @router.message(CommandStart())
    async def start_cmd(message: Message, state: FSMContext):
        await state.clear()
        admin = is_admin(config, message.from_user.id)
        await message.answer(
            "أهلاً! أنا RoboVAI Bot. اختر اللي تحبه من القائمة:",
            reply_markup=main_menu_kb(admin),
        )

    @router.message(Command("help"))
    async def help_cmd(message: Message):
        await message.answer(
            "أوامر سريعة:\n"
            "/start - القائمة الرئيسية\n"
            "/ask <سؤال> - سؤال تقني\n"
            "/links - روابطنا\n"
            "/business - خدماتنا\n"
        )

    @router.message(Command("links"))
    async def links_cmd(message: Message):
        await message.answer(links_text())

    @router.message(Command("business"))
    async def business_cmd(message: Message):
        await message.answer(business_text())

    # Inline menu
    @router.callback_query(F.data.startswith("menu:"))
    async def menu_click(call: CallbackQuery, state: FSMContext):
        action = call.data.split(":", 1)[1]
        admin = is_admin(config, call.from_user.id)

        if action == "links":
            await call.message.edit_text(links_text(), reply_markup=main_menu_kb(admin))
            await call.answer()
            return

        if action == "business":
            await call.message.edit_text(
                business_text(), reply_markup=main_menu_kb(admin)
            )
            await call.answer()
            return

        if action == "ask":
            await state.set_state(AskState.waiting_for_question)
            await call.message.edit_text(
                "اكتب سؤالك التقني الآن (مثال: ازاي أصلّح خطأ في بايثون؟)",
                reply_markup=main_menu_kb(admin),
            )
            await call.answer()
            return

        if action == "run_pipeline":
            if not admin:
                await call.answer("غير مسموح", show_alert=True)
                return

            await call.answer("تشغيل…")
            await call.message.edit_text("🚀 جاري تنفيذ النشر الآن…")

            orchestrator = ContentOrchestrator(config, db)
            try:
                result = await orchestrator.execute()
                text = (
                    "✅ تم التنفيذ\n\n"
                    f"Success: {result.success}\n"
                    f"Steps: {' -> '.join(result.steps_completed)}\n\n"
                    f"Dev.to: {result.devto_url or '-'}\n"
                    f"Blogger: {result.blogger_url or '-'}\n"
                    f"Telegram Msg: {result.telegram_message_id or '-'}\n"
                    f"Facebook Post: {result.facebook_post_id or '-'}\n"
                )
                await call.message.edit_text(text, reply_markup=main_menu_kb(admin))
            finally:
                await orchestrator.close()
            return

        if action == "settings":
            if not admin:
                await call.answer("غير مسموح", show_alert=True)
                return
            daily = db.get_setting(
                "daily_free_questions", str(DEFAULT_DAILY_FREE_QUESTIONS)
            )
            await call.message.edit_text(
                "⚙️ إعدادات سريعة\n\n"
                f"- الحد اليومي المجاني للأسئلة التقنية: {daily}\n\n"
                "لتغيير الحد: اكتب في الشات\n"
                "`/set_daily_limit 5`\n",
                reply_markup=main_menu_kb(admin),
                parse_mode=ParseMode.MARKDOWN,
            )
            await call.answer()
            return

        if action == "prompts":
            if not admin:
                await call.answer("غير مسموح", show_alert=True)
                return
            await state.clear()
            await call.message.edit_text(
                "📝 <b>تعديل البرومبت</b>\n\n"
                "اختار أي برومبت تحب تعدله.\n"
                "معلومة: التعديل بيتسجل في config.json على السيرفر.\n",
                reply_markup=prompts_menu_kb(),
                parse_mode=ParseMode.HTML,
            )
            await call.answer()
            return

        if action == "groups":
            if not admin:
                await call.answer("غير مسموح", show_alert=True)
                return
            await call.message.edit_text(
                "👥 إدارة الجروبات\n\n"
                "- داخل الجروب استخدم: /group_on أو /group_off\n"
                "- لتفعيل الرد التلقائي: /auto_on أو /auto_off\n"
                "- لتفعيل CTA: /cta_on أو /cta_off\n",
                reply_markup=main_menu_kb(admin),
            )
            await call.answer()
            return

        await call.answer()

    # Prompt editing menu
    @router.callback_query(F.data.startswith("prompts:"))
    async def prompt_pick(call: CallbackQuery, state: FSMContext):
        admin = is_admin(config, call.from_user.id)
        if not admin:
            await call.answer("غير مسموح", show_alert=True)
            return

        key = call.data.split(":", 1)[1]
        current = _get_prompt_value(config, key)
        short = (current or "").strip()
        if len(short) > 1200:
            short = short[:1200] + "…"

        await state.set_state(PromptEditState.waiting_for_prompt_text)
        await state.update_data(prompt_key=key)

        await call.message.edit_text(
            "📝 <b>تعديل البرومبت</b>\n\n"
            f"<b>النوع:</b> <code>{key}</code>\n\n"
            "<b>البرومبت الحالي (مختصر):</b>\n"
            f"<blockquote>{short}</blockquote>\n\n"
            "ابعت البرومبت الجديد بالكامل في رسالة واحدة.\n"
            "(ولو عايز تلغي: اكتب /cancel)",
            reply_markup=prompts_menu_kb(),
            parse_mode=ParseMode.HTML,
        )
        await call.answer()

    @router.message(Command("cancel"))
    async def cancel_cmd(message: Message, state: FSMContext):
        await state.clear()
        admin = is_admin(config, message.from_user.id)
        await message.answer("✅ تم الإلغاء.", reply_markup=main_menu_kb(admin))

    @router.message(PromptEditState.waiting_for_prompt_text)
    async def prompt_save(message: Message, state: FSMContext):
        admin = is_admin(config, message.from_user.id)
        if not admin:
            await message.answer("غير مسموح")
            await state.clear()
            return

        data = await state.get_data()
        key = data.get("prompt_key")
        new_prompt = (message.text or "").strip()

        if not key or not new_prompt:
            await message.answer("⚠️ ابعت البرومبت كنص واضح.")
            return

        ok = _update_prompt(config, key, new_prompt)
        if ok:
            # Best-effort reload for long-running workers
            try:
                config.reload()
            except Exception:
                pass
            await message.answer(
                "✅ تمام! اتسجل البرومبت الجديد.\n" "هيتطبق على أول نشر جاي.",
                reply_markup=main_menu_kb(admin),
            )
        else:
            await message.answer(
                "❌ حصلت مشكلة وأنا بحفظ البرومبت. جرّب تاني.",
                reply_markup=main_menu_kb(admin),
            )

        await state.clear()

    # Admin: set daily limit
    @router.message(Command("set_daily_limit"))
    async def set_daily_limit(message: Message):
        if not is_admin(config, message.from_user.id):
            return
        parts = (message.text or "").split()
        if len(parts) != 2 or not parts[1].isdigit():
            await message.answer("استخدم: /set_daily_limit 5")
            return
        db.set_setting("daily_free_questions", parts[1])
        await message.answer(f"✅ تم تحديث الحد اليومي إلى: {parts[1]}")

    # Q&A command
    @router.message(Command("ask"))
    async def ask_cmd(message: Message):
        question = (message.text or "").split(" ", 1)
        if len(question) < 2 or not question[1].strip():
            await message.answer("اكتب: /ask سؤالك هنا")
            return
        await handle_question(message, config, db, llm, question[1].strip())

    # FSM Q&A
    @router.message(AskState.waiting_for_question)
    async def ask_state(message: Message, state: FSMContext):
        await state.clear()
        q = (message.text or "").strip()
        if not q:
            await message.answer("اكتب سؤال واضح.")
            return
        await handle_question(message, config, db, llm, q)

    # Group settings commands
    @router.message(Command("group_on"))
    async def group_on(message: Message):
        if message.chat.type in ("private",):
            return
        db.update_group_settings(message.chat.id, enabled=True)
        await message.answer("✅ تم تفعيل البوت في هذا الجروب")

    @router.message(Command("group_off"))
    async def group_off(message: Message):
        if message.chat.type in ("private",):
            return
        db.update_group_settings(message.chat.id, enabled=False)
        await message.answer("🛑 تم إيقاف البوت في هذا الجروب")

    @router.message(Command("auto_on"))
    async def auto_on(message: Message):
        if message.chat.type in ("private",):
            return
        db.update_group_settings(message.chat.id, auto_reply=True)
        await message.answer("✅ تم تفعيل الرد التلقائي")

    @router.message(Command("auto_off"))
    async def auto_off(message: Message):
        if message.chat.type in ("private",):
            return
        db.update_group_settings(message.chat.id, auto_reply=False)
        await message.answer("🛑 تم إيقاف الرد التلقائي")

    @router.message(Command("cta_on"))
    async def cta_on(message: Message):
        if message.chat.type in ("private",):
            return
        db.update_group_settings(message.chat.id, cta_enabled=True)
        await message.answer("✅ تم تفعيل CTA")

    @router.message(Command("cta_off"))
    async def cta_off(message: Message):
        if message.chat.type in ("private",):
            return
        db.update_group_settings(message.chat.id, cta_enabled=False)
        await message.answer("🛑 تم إيقاف CTA")

    # Basic group auto-reply (only when enabled + auto_reply)
    @router.message(F.chat.type.in_({"group", "supergroup"}))
    async def group_autoreply(message: Message):
        settings = db.get_group_settings(message.chat.id)
        if not settings["enabled"] or not settings["auto_reply"]:
            return

        text = (message.text or "").strip()
        if not text:
            return

        # Lightweight trigger: messages starting with "?" or "سؤال"
        if not (
            text.startswith("?") or text.startswith("سؤال") or text.startswith("/ask")
        ):
            return

        q = text
        if text.startswith("/ask"):
            q = text.split(" ", 1)[1] if " " in text else ""
        if not q:
            return

        await handle_question(
            message, config, db, llm, q, language=settings.get("language", "ar")
        )

    dp.include_router(router)
    return dp, bot, config, db, llm


async def main():
    dp, bot, config, db, llm = await build_app()
    acquired_lock = False
    try:
        # Best-effort: ensure we're in polling mode and clear any webhook.
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass

        # Avoid TelegramConflictError during deploy overlap by using a simple lock.
        lock_path = Path(os.getenv("TG_POLL_LOCK_PATH", "data/telegram_polling.lock"))
        stale_seconds = int(os.getenv("TG_POLL_LOCK_STALE_SECONDS", "600"))
        max_wait_seconds = int(os.getenv("TG_POLL_LOCK_MAX_WAIT_SECONDS", "120"))
        started_wait = datetime.utcnow().timestamp()

        lock_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(str(datetime.utcnow().timestamp()))
                acquired_lock = True
                break
            except FileExistsError:
                try:
                    age = datetime.utcnow().timestamp() - lock_path.stat().st_mtime
                except Exception:
                    age = 0

                if age > stale_seconds:
                    try:
                        lock_path.unlink(missing_ok=True)
                        continue
                    except Exception:
                        pass

                if datetime.utcnow().timestamp() - started_wait > max_wait_seconds:
                    logger.warning(
                        "Telegram polling lock still held; skipping polling to avoid conflicts."
                    )
                    return

                await asyncio.sleep(3)

        logger.info("🤖 Telegram Chatbot started (polling)")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        try:
            if acquired_lock:
                Path(
                    os.getenv("TG_POLL_LOCK_PATH", "data/telegram_polling.lock")
                ).unlink(missing_ok=True)
        except Exception:
            pass
        try:
            await llm.close()
        except Exception:
            pass
        try:
            await bot.session.close()
        except Exception:
            pass
        db.close()


async def start_chatbot():
    """Entry point for running chatbot from unified_bot.py"""
    await main()


if __name__ == "__main__":
    asyncio.run(main())
