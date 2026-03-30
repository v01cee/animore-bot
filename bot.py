"""ANIMØRE Bot — downloads TikTok videos and saves metadata to Notion."""

import os
import re
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

from config import TELEGRAM_TOKEN, TELEGRAM_FILE_LIMIT_MB
from downloader import download_video
from notion_service import link_exists, create_page

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Matches tiktok.com and vt.tiktok.com links
TIKTOK_URL_RE = re.compile(r"https?://(?:www\.|vt\.|vm\.)?tiktok\.com/\S+")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Hi! Send me a TikTok link and I'll download the video and save it to Notion."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming messages — expect TikTok links."""
    text = update.message.text or ""
    match = TIKTOK_URL_RE.search(text)

    if not match:
        await update.message.reply_text("Send me a TikTok link.")
        return

    url = match.group(0)

    # --- Deduplication ---
    try:
        if link_exists(url):
            await update.message.reply_text("⚠️ Already in the database.")
            return
    except Exception as e:
        logger.error("Notion check failed: %s", e)
        # Continue anyway — better to download than to block

    # --- Download ---
    await update.message.reply_text("⏳ Downloading...")

    try:
        file_path, username = download_video(url)
    except Exception as e:
        logger.error("Download failed: %s", e)
        await update.message.reply_text("❌ Could not download. Check the link.")
        return

    # --- Send video ---
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if file_size_mb > TELEGRAM_FILE_LIMIT_MB:
            await update.message.reply_text(
                f"❌ Video is too large ({file_size_mb:.1f} MB). "
                f"Telegram limit is {TELEGRAM_FILE_LIMIT_MB} MB."
            )
        else:
            with open(file_path, "rb") as video_file:
                await update.message.reply_video(video=video_file)
    except Exception as e:
        logger.error("Failed to send video: %s", e)
        await update.message.reply_text("❌ Failed to send the video.")
    finally:
        # Clean up downloaded file
        if os.path.exists(file_path):
            os.remove(file_path)

    # --- Save to Notion ---
    try:
        create_page(username=username, url=url)
        await update.message.reply_text("✅ Done. Saved to Notion.")
    except Exception as e:
        logger.error("Notion save failed: %s", e)
        await update.message.reply_text("❌ Downloaded but failed to save to Notion.")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set. Check your .env file.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
