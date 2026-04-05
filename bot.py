"""ANIMØRE Bot — скачивает TikTok видео и сохраняет метаданные в Notion."""

import os
import re
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.request import HTTPXRequest

from config import TELEGRAM_TOKEN, TELEGRAM_FILE_LIMIT_MB, ADMIN_IDS
from downloader import download_video
from notion_service import get_titles, get_page_by_url, create_page

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TIKTOK_URL_RE = re.compile(r"https?://(?:www\.|vt\.|vm\.)?tiktok\.com/\S+")


def is_admin(update: Update) -> bool:
    return update.effective_user and update.effective_user.id in ADMIN_IDS


def format_views(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def build_category_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """Строит инлайн-клавиатуру с кнопками тайтлов (по 2 в ряд) + кнопка пропуска."""
    buttons = [InlineKeyboardButton(cat, callback_data=f"cat:{cat}") for cat in categories]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("➡️ Без тайтла", callback_data="cat:")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return
    await update.message.reply_text(
        "👋 Привет! Отправь мне ссылку на TikTok — скачаю видео и сохраню в Notion."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    text = update.message.text or ""
    match = TIKTOK_URL_RE.search(text)

    if not match:
        await update.message.reply_text("Отправь мне ссылку на TikTok.")
        return

    url = match.group(0)

    # --- Проверка дубликатов ---
    try:
        existing = get_page_by_url(url)
    except Exception as e:
        logger.error("Ошибка проверки Notion: %s", e)
        existing = None

    if existing:
        await _handle_existing(update, context, existing, url)
        return

    # --- Скачивание ---
    await update.message.reply_text("⏳ Скачиваю...")

    # Подтягиваем тайтлы из Notion параллельно со скачиванием
    try:
        categories = get_titles()
    except Exception as e:
        logger.error("Ошибка получения тайтлов: %s", e)
        categories = []

    try:
        file_path, username, video_url, view_count = download_video(url)
    except Exception as e:
        logger.error("Ошибка скачивания: %s", e)
        await update.message.reply_text("❌ Не удалось скачать. Проверь ссылку.")
        return

    # --- Отправка видео ---
    sent = False
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if file_size_mb > TELEGRAM_FILE_LIMIT_MB:
            await update.message.reply_text(
                f"⚠️ Видео слишком большое ({file_size_mb:.1f} МБ). Лимит Telegram — {TELEGRAM_FILE_LIMIT_MB} МБ."
            )
        else:
            with open(file_path, "rb") as video_file:
                await update.message.reply_video(
                    video=video_file,
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=30,
                )
            sent = True
    except Exception as e:
        logger.error("Ошибка отправки видео: %s", e)
        await update.message.reply_text("❌ Не удалось отправить видео.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if not sent:
        return

    # --- Сохраняем состояние и показываем кнопки категорий ---
    context.user_data["pending"] = {
        "url": url,
        "username": username,
        "video_url": video_url,
        "view_count": view_count,
    }

    views_str = f"👁 {format_views(view_count)}" if view_count else ""
    caption = f"👤 @{username}"
    if views_str:
        caption += f"  {views_str}"
    caption += "\n\nВыбери аниме:"

    if categories:
        await update.message.reply_text(
            caption,
            reply_markup=build_category_keyboard(categories),
        )
    else:
        # Если тайтлов нет — сохраняем без тайтла
        try:
            create_page(username=username, url=url)
            await update.message.reply_text(f"{caption}\n\n✅ Сохранено в Notion.")
        except Exception as e:
            logger.error("Ошибка сохранения в Notion: %s", e)
            await update.message.reply_text("❌ Не удалось сохранить в Notion.")


async def _handle_existing(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: dict,
    url: str,
) -> None:
    """Обрабатывает ссылку, которая уже есть в Notion — переотправляет видео и инфо."""
    props = page.get("properties", {})

    # Достаём данные из Notion
    title_list = props.get("Content Creator", {}).get("title", [])
    username = title_list[0]["text"]["content"] if title_list else "unknown"

    categories = [opt["name"] for opt in props.get("Category", {}).get("multi_select", [])]
    category_str = ", ".join(categories) if categories else "—"

    # Ссылка на видео из Files & media
    files = props.get("Files & media", {}).get("files", [])
    video_url = files[0].get("external", {}).get("url", "") if files else ""

    # Всегда скачиваем заново по оригинальной TikTok ссылке
    # (CDN ссылки из Notion быстро истекают)
    file_path = None
    try:
        await update.message.reply_text("⏳ Скачиваю видео...")
        file_path, _, _, view_count = download_video(url)

        # Обновляем инфо с просмотрами
        views_str = f"  👁 {format_views(view_count)}" if view_count else ""
        await update.message.reply_text(
            f"⚠️ Уже есть в базе:\n"
            f"👤 @{username}{views_str}\n"
            f"📁 {category_str}"
        )

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if file_size_mb > TELEGRAM_FILE_LIMIT_MB:
            await update.message.reply_text(
                f"⚠️ Видео слишком большое ({file_size_mb:.1f} МБ)."
            )
        else:
            with open(file_path, "rb") as vf:
                await update.message.reply_video(
                    video=vf,
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=30,
                )
    except Exception as e:
        logger.error("Ошибка переотправки видео: %s", e)
        await update.message.reply_text("❌ Не удалось скачать видео.")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатие кнопки категории."""
    query = update.callback_query
    await query.answer()

    if not (update.effective_user and update.effective_user.id in ADMIN_IDS):
        return

    category = query.data.replace("cat:", "", 1)
    pending = context.user_data.get("pending")

    if not pending:
        await query.edit_message_text("❌ Данные устарели. Отправь ссылку заново.")
        return

    try:
        create_page(
            username=pending["username"],
            url=pending["url"],
            title=category,
        )
        views_str = f"  👁 {format_views(pending['view_count'])}" if pending.get("view_count") else ""
        await query.edit_message_text(
            f"✅ Сохранено в Notion.\n"
            f"👤 @{pending['username']}{views_str}\n"
            f"🎬 {category}"
        )
        context.user_data.pop("pending", None)
    except Exception as e:
        logger.error("Ошибка сохранения в Notion: %s", e)
        await query.edit_message_text("❌ Не удалось сохранить в Notion.")


def main() -> None:
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не задан. Проверь .env файл.")

    request = HTTPXRequest(read_timeout=120, write_timeout=120, connect_timeout=30)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_category, pattern=r"^cat:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
