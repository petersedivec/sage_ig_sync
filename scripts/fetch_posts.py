#!/usr/bin/env python3
"""
fetch_posts.py — Instagram Graph API fetcher for @songs.by.sage
─────────────────────────────────────────────────────────────────
Runs daily via GitHub Actions.
  1. Refreshes the long-lived access token (valid 60 days)
  2. Fetches all recent posts from the Instagram Graph API
  3. Downloads cover thumbnails to docs/images/<id>.jpg
  4. Writes docs/posts.json
"""

import os
import json
import sys
import requests
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────

ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
if not ACCESS_TOKEN:
    sys.exit("ERROR: INSTAGRAM_ACCESS_TOKEN env var is not set.")

API_BASE  = "https://graph.instagram.com/v18.0"
FIELDS    = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
MAX_POSTS = 50

ROOT      = Path(__file__).parent.parent
DOCS      = ROOT / "docs"
IMG_DIR   = DOCS / "images"
JSON_OUT  = DOCS / "posts.json"


# ── Token refresh ─────────────────────────────────────────────────────────────

def refresh_token(token: str) -> str:
    """
    Refresh a long-lived IG token.  Writes NEW_ACCESS_TOKEN to GITHUB_ENV so
    the workflow can update the Actions secret automatically.
    """
    r = requests.get(
        f"{API_BASE}/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
        timeout=15,
    )
    r.raise_for_status()
    new = r.json().get("access_token", token)

    gh_env = os.environ.get("GITHUB_ENV")
    if gh_env and new != token:
        with open(gh_env, "a") as f:
            f.write(f"NEW_ACCESS_TOKEN={new}\n")
        print("✓ Access token refreshed — secret will be updated.")
    else:
        print("✓ Access token still fresh.")

    return new


# ── Media fetch ───────────────────────────────────────────────────────────────

def fetch_all_media(token: str) -> list[dict]:
    """Paginate through /me/media until we have MAX_POSTS or run out."""
    posts  = []
    url    = f"{API_BASE}/me/media"
    params = {"fields": FIELDS, "access_token": token, "limit": 25}

    while url and len(posts) < MAX_POSTS:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        posts.extend(data.get("data", []))
        url    = data.get("paging", {}).get("next")
        params = {}  # 'next' URL already has all params encoded

    return posts[:MAX_POSTS]


# ── Thumbnail download ────────────────────────────────────────────────────────

def download_thumb(post: dict) -> str | None:
    """
    Download the cover image for a post.
    - Reels / VIDEO → thumbnail_url (static frame)
    - IMAGE         → media_url
    - CAROUSEL      → media_url of first item
    Returns the relative path from docs/, e.g. 'images/123456789.jpg', or None.
    """
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    media_type = post.get("media_type", "IMAGE")
    if media_type == "VIDEO":
        url = post.get("thumbnail_url") or post.get("media_url")
    else:
        url = post.get("media_url") or post.get("thumbnail_url")

    if not url:
        print(f"  ⚠ No image URL for {post['id']}, skipping.")
        return None

    post_id  = post["id"]
    img_path = IMG_DIR / f"{post_id}.jpg"

    # Skip if already on disk — avoids re-downloading on every run
    if img_path.exists() and img_path.stat().st_size > 0:
        return f"images/{post_id}.jpg"

    try:
        r = requests.get(url, timeout=30, stream=True)
        r.raise_for_status()
        with open(img_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  ↓ images/{post_id}.jpg")
        return f"images/{post_id}.jpg"
    except Exception as e:
        print(f"  ✗ Failed to download {post_id}: {e}")
        return None


# ── Record builder ────────────────────────────────────────────────────────────

def make_record(post: dict, thumb_path: str | None) -> dict:
    return {
        "id":         post["id"],
        "caption":    post.get("caption", ""),
        "media_type": post.get("media_type", "IMAGE"),
        "permalink":  post["permalink"],
        "timestamp":  post["timestamp"],
        "thumbnail":  thumb_path,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print("═" * 50)
    print("  Songs by Sage · Instagram feed updater")
    print("═" * 50)

    # Step 1 — refresh token
    token = refresh_token(ACCESS_TOKEN)

    # Step 2 — fetch posts
    print(f"\nFetching media from Instagram API…")
    raw = fetch_all_media(token)
    print(f"✓ {len(raw)} posts found")

    # Step 3 — download thumbnails
    print(f"\nDownloading thumbnails…")
    records = []
    for post in raw:
        thumb = download_thumb(post)
        records.append(make_record(post, thumb))

    # Step 4 — write JSON
    DOCS.mkdir(parents=True, exist_ok=True)
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"\n✓ docs/posts.json written ({len(records)} posts)")
    print("═" * 50)


if __name__ == "__main__":
    main()
