# ANIMØRE Bot

Telegram bot that downloads TikTok videos and saves metadata to a Notion database.

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and find [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name (e.g., "ANIMØRE Bot") and a username (e.g., `animore_bot`)
4. Copy the **API token** — you'll need it for `.env`

### 2. Create a Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"New integration"**
3. Name it (e.g., "ANIMØRE Bot"), select your workspace
4. Copy the **Internal Integration Token** (starts with `ntn_`)
5. In your Notion database page, click **⋯ → Connections → Connect to "ANIMØRE Bot"**

### 3. Set Up the Notion Database

Create a database in Notion with these properties:

| Property | Type |
|---|---|
| Content Creator | Title |
| Link | URL |
| Category | Select (add option "Anime") |
| Checkbox | Checkbox |

To get the **database ID**: open the database as a full page — the URL looks like:
```
https://www.notion.so/<workspace>/<DATABASE_ID>?v=...
```
Copy the 32-character hex ID (the part before `?v=`). Format it with dashes or use as-is — both work.

### 4. Configure Environment

```bash
cp .env.example .env
```

Fill in your `.env`:
```
TELEGRAM_TOKEN=123456:ABC-DEF...
NOTION_TOKEN=ntn_...
NOTION_DATABASE_ID=abc123...
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** yt-dlp requires [ffmpeg](https://ffmpeg.org/download.html) for some formats. Install it if you don't have it.

### 6. Run Locally

```bash
python bot.py
```

## Deploy to Railway

1. Push this project to a GitHub repo
2. Go to [railway.app](https://railway.app) and create a new project
3. Select **"Deploy from GitHub repo"** and connect your repo
4. Go to **Variables** tab and add:
   - `TELEGRAM_TOKEN`
   - `NOTION_TOKEN`
   - `NOTION_DATABASE_ID`
5. Railway auto-detects Python. If it doesn't, add a `Procfile`:
   ```
   worker: python bot.py
   ```
6. Deploy. The bot will start polling automatically.

> Railway's free tier gives you $5/month of usage — more than enough for a personal bot.

## Usage

Send any TikTok link to the bot. It will:
1. Check if the link is already in Notion (deduplication)
2. Download the video without watermark
3. Send the video back to you in Telegram
4. Create a new entry in your Notion database

## Project Structure

```
animore-bot/
├── bot.py              # Main entry point, Telegram handlers
├── downloader.py       # yt-dlp download logic
├── notion_client.py    # Notion API: dedup check + page creation
├── config.py           # Loads .env variables
├── .env.example        # Template for secrets
├── requirements.txt    # Python dependencies
└── README.md           # This file
```
