"""Скачивание TikTok видео через tikwm.com API (без водяного знака)."""

import os
import re
import tempfile
import requests


def extract_username(url: str) -> str:
    """Извлекает @username из ссылки на TikTok."""
    match = re.search(r"tiktok\.com/@([^/?\s]+)", url)
    return match.group(1) if match else ""


def download_video(url: str) -> tuple[str, str, str, int]:
    """Скачивает видео и возвращает (путь_к_файлу, username, video_url, view_count)."""
    api_url = "https://www.tikwm.com/api/"
    resp = requests.get(api_url, params={"url": url, "hd": 1}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise Exception(data.get("msg", "API error"))

    video_data = data["data"]
    video_url = video_data.get("hdplay") or video_data.get("play")

    if not video_url:
        raise Exception("Не удалось получить ссылку на видео")

    # Username
    username = extract_username(url)
    if not username:
        author = video_data.get("author", {})
        username = (
            author.get("unique_id")
            or author.get("nickname")
            or "unknown"
        )

    # Просмотры
    view_count = video_data.get("play_count", 0) or 0

    # Скачиваем видео
    tmp_dir = tempfile.mkdtemp(prefix="animore_")
    file_path = os.path.join(tmp_dir, f"{video_data.get('id', 'video')}.mp4")

    video_resp = requests.get(video_url, timeout=120)
    video_resp.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(video_resp.content)

    return file_path, username, video_url, view_count


def fetch_video_from_url(video_url: str, filename: str = "video") -> str:
    """Скачивает видео по прямой ссылке и возвращает путь к файлу."""
    tmp_dir = tempfile.mkdtemp(prefix="animore_")
    file_path = os.path.join(tmp_dir, f"{filename}.mp4")

    resp = requests.get(video_url, timeout=120)
    resp.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(resp.content)

    return file_path
