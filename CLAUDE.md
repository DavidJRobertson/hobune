# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Hobune is a static HTML generator for self-hosted yt-dlp video archives. It reads `.info.json` files produced by yt-dlp, then writes a tree of HTML pages (channel indexes, video watch pages, comments pages) into an output directory served by a web server.

## Running it

```bash
# Set up venv and install deps
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Configure (first run copies default.json → config.json)
cp default.json config.json   # then edit config.json

# Generate HTML
.venv/bin/python hobune.py
```

There are no tests, no lint step, and no build step.

## Architecture

The entry point is `hobune/__main__.py`. Execution has four phases:

1. **`init_assets`** — creates the Jinja2 `Environment` (loader points at `templates/`, autoescape on, custom filters `nl2br` and `url_quote` registered), creates output subdirs, copies static assets.
2. **`initialize_channels`** — walks `config.files_path` recursively, reads every `.info.json`, and builds a `channels` dict (`channel_id → HobuneChannel`). Videos are keyed under their channel; duplicates are deduplicated.
3. **`update_templates`** — sets Jinja2 globals (`web_root`, `site_name`, `html_ext`, `custom_pages`) and writes `index.html` + any custom pages from `custom/`.
4. **`create_video_pages`** / **`create_channel_pages`** — iterate channels/videos and call `tmpl.render(...)` with data dicts, writing one `.html` file per video/channel.

### Templates (`templates/`)

All templates use Jinja2 with `{% extends "base.html" %}` / `{% block content %}`. `base.html` provides the shared nav; page-specific templates fill the `content` block. Global variables (`web_root`, `site_name`, `html_ext`, `custom_pages`) are available in every template via `env.globals` — don't pass them explicitly to `render()`.

| Template | Used for |
|---|---|
| `base.html` | Shared nav wrapper |
| `video.html` | Individual video watch page |
| `channel.html` | Individual channel page (video grid) |
| `channels.html` | Channels index |
| `index.html` | Home page |
| `comments.html` | Comments page (optional feature) |
| `custom_page.html` | Wrapper for raw HTML files in `custom/` |

### Customisation points

- **`custom/`** — drop any `.html` file here; it gets wrapped in `base.html` and written to the output root. A nav link is added automatically.
- **`note/`** — drop a file named after a channel ID (dots replaced with underscores) to inject a raw HTML note at the top of that channel's page.
- **`is_full_channel(root)`** in `channels.py` — controls whether a video's directory maps to a named channel or falls into the catch-all "other" bucket. Override this to filter by path.

### Comments (disabled by default)

`hobune/comments.py` has `comments_enabled = False` and `comments_path` hardcoded. Enable and point it at a directory of `VIDEOID.jsonl` files. The `textDisplay` field from the YouTube API is rendered with `| safe` (intentional — it contains YouTube-provided HTML); don't enable comments unless the data source is trusted.

### Config fields (`config.json`)

| Field | Purpose |
|---|---|
| `files_path` | Local path where yt-dlp files live |
| `files_web_path` | Web-accessible URL prefix for those files |
| `web_root` | URL prefix for generated pages |
| `output_path` | Where to write the generated HTML |
| `add_html_ext` | Whether links end in `.html` |
| `removed_videos_file` | Newline-separated file; last 11 chars of each line treated as a video ID |
| `unlisted_videos_file` | Same format, marks videos as unlisted |
