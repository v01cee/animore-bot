"""Notion API — проверка дубликатов и создание записей."""

from notion_client import Client
from config import NOTION_TOKEN, NOTION_DATABASE_ID

notion = Client(auth=NOTION_TOKEN)


def link_exists(url: str) -> bool:
    """Проверяет, есть ли ссылка уже в базе Notion."""
    response = notion.databases.query(
        **{
            "database_id": NOTION_DATABASE_ID,
            "filter": {"property": "Link", "url": {"equals": url}},
        }
    )
    return len(response["results"]) > 0


def create_page(username: str, url: str, category: str = "Anime") -> None:
    """Создаёт новую запись в базе Notion."""
    notion.pages.create(
        **{
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Content Creator": {
                    "title": [{"text": {"content": username}}],
                },
                "Link": {"url": url},
                "Category": {"select": {"name": category}},
                "Checkbox": {"checkbox": False},
            },
        }
    )
