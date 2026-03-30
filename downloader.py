"""Скачивание видео через yt-dlp — TikTok без водяного знака."""

import os
import re
import tempfile
import yt_dlp

from config import PROXY_URL


def extract_username(url: str) -> str:
    """Извлекает @username из ссылки на TikTok."""
    match = re.search(r"tiktok\.com/@([^/?\s]+)", url)
    return match.group(1) if match else ""


def download_video(url: str) -> tuple[str, str]:
    """Скачивает видео и возвращает (путь_к_файлу, username)."""
    tmp_dir = tempfile.mkdtemp(prefix="animore_")
    output_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    if PROXY_URL:
        ydl_opts["proxy"] = PROXY_URL

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

        username = extract_username(url)
        if not username:
            username = (
                info.get("uploader")
                or info.get("channel")
                or info.get("uploader_id")
                or "unknown"
            )

    return file_path, username
