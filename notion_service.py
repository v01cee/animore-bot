"""Notion API через requests — проверка дубликатов и создание записей."""

import logging
import requests
from config import NOTION_TOKEN, NOTION_DATABASE_ID

logger = logging.getLogger(__name__)

NOTION_API = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def link_exists(url: str) -> bool:
    """Проверяет, есть ли ссылка уже в базе Notion."""
    resp = requests.post(
        f"{NOTION_API}/databases/{NOTION_DATABASE_ID}/query",
        headers=HEADERS,
        json={"filter": {"property": "Link", "url": {"equals": url}}},
        timeout=15,
    )
    if not resp.ok:
        logger.error("Notion query error: %s", resp.text)
    resp.raise_for_status()
    return len(resp.json()["results"]) > 0


def create_page(username: str, url: str, category: str = "Anime") -> None:
    """Создаёт новую запись в базе Notion."""
    resp = requests.post(
        f"{NOTION_API}/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Content Creator": {
                    "title": [{"text": {"content": username}}],
                },
                "Link": {"url": url},
                "Category": {"multi_select": [{"name": category}]},
                "Checkbox": {"checkbox": False},
            },
        },
        timeout=15,
    )
    if not resp.ok:
        logger.error("Notion create error: %s", resp.text)
    resp.raise_for_status()
