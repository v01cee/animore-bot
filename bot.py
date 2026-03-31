"""ANIMØRE Bot — скачивает TikTok видео и сохраняет метаданные в Notion."""

import os
import re
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

from config import TELEGRAM_TOKEN, TELEGRAM_FILE_LIMIT_MB, ADMIN_IDS
from downloader import download_video
from notion_service import link_exists, create_page

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Matches tiktok.com and vt.tiktok.com links
TIKTOK_URL_RE = re.compile(r"https?://(?:www\.|vt\.|vm\.)?tiktok\.com/\S+")


def is_admin(update: Update) -> bool:
    """Проверяет, является ли пользователь админом."""
    return update.effective_user and update.effective_user.id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /start."""
    if not is_admin(update):
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    await update.message.reply_text(
        "👋 Привет! Отправь мне ссылку на TikTok — скачаю видео и сохраню в Notion."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка входящих сообщений — ожидаем ссылки на TikTok."""
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
        if link_exists(url):
            await update.message.reply_text("⚠️ Уже есть в базе.")
            return
    except Exception as e:
        logger.error("Ошибка проверки Notion: %s", e)

    # --- Скачивание ---
    await update.message.reply_text("⏳ Скачиваю...")

    try:
        file_path, username, video_url = download_video(url)
    except Exception as e:
        logger.error("Ошибка скачивания: %s", e)
        await update.message.reply_text("❌ Не удалось скачать. Проверь ссылку.")
        return

    # --- Отправка видео ---
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if file_size_mb > TELEGRAM_FILE_LIMIT_MB:
            await update.message.reply_text(
                f"❌ Видео слишком большое ({file_size_mb:.1f} МБ). "
                f"Лимит Telegram — {TELEGRAM_FILE_LIMIT_MB} МБ."
            )
        else:
            with open(file_path, "rb") as video_file:
                await update.message.reply_video(
                    video=video_file,
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=30,
                )
    except Exception as e:
        logger.error("Ошибка отправки видео: %s", e)
        await update.message.reply_text("❌ Не удалось отправить видео.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    # --- Сохранение в Notion ---
    try:
        create_page(username=username, url=url, video_url=video_url)
        await update.message.reply_text("✅ Готово. Сохранено в Notion.")
    except Exception as e:
        logger.error("Ошибка сохранения в Notion: %s", e)
        await update.message.reply_text("❌ Скачал, но не удалось сохранить в Notion.")


def main() -> None:
    """Запуск бота."""
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не задан. Проверь .env файл.")

    # Увеличиваем таймауты для загрузки больших видео
    request = HTTPXRequest(read_timeout=120, write_timeout=120, connect_timeout=30)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
