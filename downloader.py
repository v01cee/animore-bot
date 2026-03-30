"""Video downloader using yt-dlp — downloads TikTok videos without watermark."""

import os
import re
import tempfile
import yt_dlp


def extract_username(url: str) -> str:
    """Extract @username from a TikTok URL.

    Supports formats like:
      https://www.tiktok.com/@username/video/1234567890
      https://vt.tiktok.com/ZSxxxxxxx/
    For short links, the username is resolved after download from metadata.
    """
    match = re.search(r"tiktok\.com/@([^/?\s]+)", url)
    return match.group(1) if match else ""


def download_video(url: str) -> tuple[str, str]:
    """Download a TikTok video and return (file_path, username).

    Returns the path to the downloaded .mp4 and the creator's username.
    Raises Exception on failure.
    """
    tmp_dir = tempfile.mkdtemp(prefix="animore_")
    output_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

        # Try to get username from metadata if not in URL
        username = extract_username(url)
        if not username:
            # yt-dlp often provides uploader or channel
            username = (
                info.get("uploader")
                or info.get("channel")
                or info.get("uploader_id")
                or "unknown"
            )

    return file_path, username
