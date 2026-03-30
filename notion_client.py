"""Notion API client — deduplication check and page creation."""

from notion_client import Client
from config import NOTION_TOKEN, NOTION_DATABASE_ID

notion = Client(auth=NOTION_TOKEN)


def link_exists(url: str) -> bool:
    """Check if a TikTok link already exists in the Notion database."""
    response = notion.databases.query(
        database_id=NOTION_DATABASE_ID,
        filter={"property": "Link", "url": {"equals": url}},
    )
    return len(response["results"]) > 0


def create_page(username: str, url: str, category: str = "Anime") -> None:
    """Create a new page in the Notion database.

    Fields:
      - Content Creator (title) — the @username
      - Link (url) — original TikTok link
      - Category (select) — default "Anime"
      - Checkbox (checkbox) — unchecked
    """
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            "Content Creator": {
                "title": [{"text": {"content": username}}],
            },
            "Link": {"url": url},
            "Category": {"select": {"name": category}},
            "Checkbox": {"checkbox": False},
        },
    )
