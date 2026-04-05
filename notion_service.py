"""Notion API через requests — проверка дубликатов, создание записей, получение категорий."""

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


def get_categories() -> list[str]:
    """Получает список всех категорий из схемы базы Notion."""
    resp = requests.get(
        f"{NOTION_API}/databases/{NOTION_DATABASE_ID}",
        headers=HEADERS,
        timeout=15,
    )
    if not resp.ok:
        logger.error("Notion get database error: %s", resp.text)
        return []
    data = resp.json()
    options = (
        data.get("properties", {})
        .get("Category", {})
        .get("multi_select", {})
        .get("options", [])
    )
    return [opt["name"] for opt in options]


def get_page_by_url(url: str) -> dict | None:
    """Возвращает страницу из Notion по ссылке или None."""
    resp = requests.post(
        f"{NOTION_API}/databases/{NOTION_DATABASE_ID}/query",
        headers=HEADERS,
        json={"filter": {"property": "Link", "url": {"equals": url}}},
        timeout=15,
    )
    if not resp.ok:
        logger.error("Notion query error: %s", resp.text)
        resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def create_page(username: str, url: str, category: str = "Anime") -> None:
    """Создаёт новую запись в базе Notion."""
    properties = {
        "Content Creator": {
            "title": [{"text": {"content": username}}],
        },
        "Link": {"url": url},
        "Category": {"multi_select": [{"name": category}]},
        "Checkbox": {"checkbox": False},
    }

    resp = requests.post(
        f"{NOTION_API}/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": properties,
        },
        timeout=15,
    )
    if not resp.ok:
        logger.error("Notion create error: %s", resp.text)
    resp.raise_for_status()
