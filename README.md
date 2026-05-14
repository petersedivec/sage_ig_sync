# Songs by Sage · Music Gallery

Automated music gallery for [@songs.by.sage](https://www.instagram.com/songs.by.sage).
Built on GitHub Pages with daily auto-updates via GitHub Actions + Instagram Graph API.

**Live site:** [music.sailingwithsage.com](https://music.sailingwithsage.com)

---

## How it works

```
Instagram API  →  fetch_posts.py  →  posts.json + images/  →  GitHub Pages
                       ↑
               GitHub Actions (daily cron)
```

1. GitHub Actions triggers daily at 10:00 UTC
2. `scripts/fetch_posts.py` hits the Instagram Graph API, downloads cover thumbnails, and writes `docs/posts.json`
3. Changes are committed back to the repo
4. GitHub Pages auto-serves `docs/index.html`, which loads the posts dynamically

---

## Setup guide

### Step 1 — Create the GitHub repo

Create a new repo (public or private) and push this code to it.

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/songs-by-sage.git
git push -u origin main
```

### Step 2 — Switch to a Creator account on Instagram

Instagram → **Settings → Account → Switch to Professional Account → Creator**

It's free, reversible, and required for API access. Followers and content are unaffected.

### Step 3 — Create a Meta Developer App

1. Go to [developers.facebook.com](https://developers.facebook.com) → **My Apps → Create App**
2. Choose **"Other"** as the use case, then **"Consumer"** as the app type
3. Inside the app, click **Add Product → Instagram**
4. Go to **Instagram → API Setup with Instagram Login**
5. Add Sage's Instagram account as a tester (or log in directly)
6. Generate a **long-lived user access token**
   - Tokens last 60 days; the script auto-refreshes them on every daily run

### Step 4 — Add the token as a GitHub secret

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `INSTAGRAM_ACCESS_TOKEN` | Your long-lived token from Step 3 |

### Step 5 — Enable GitHub Pages

In your repo: **Settings → Pages**
- Source: **Deploy from a branch**
- Branch: `main`, Folder: `/docs`

Your site will be live at `https://YOUR_USERNAME.github.io/songs-by-sage/`

### Step 6 — Custom domain

To use `music.sailingwithsage.com`:

1. In your DNS (wherever sailingwithsage.com is managed), add a `CNAME` record:
   ```
   music  →  YOUR_USERNAME.github.io
   ```
2. In GitHub Pages settings, add `music.sailingwithsage.com` as the custom domain
3. Enable **Enforce HTTPS** once the cert is issued (a few minutes)

The `docs/CNAME` file is already in the repo — GitHub reads this automatically.

### Step 7 — First run

Trigger the first run manually:
**Actions → Update Instagram Feed → Run workflow**

This will fetch all posts, download thumbnails, and push everything to the repo.

---

## Running locally

```bash
# Install deps
pip install requests

# Set your token
export INSTAGRAM_ACCESS_TOKEN=your_token_here

# Run the fetcher
python scripts/fetch_posts.py

# Preview in browser
cd docs && python -m http.server 8000
# Open http://localhost:8000
```

---

## File structure

```
songs-by-sage/
├── .github/
│   └── workflows/
│       └── update-feed.yml     ← daily cron job
├── scripts/
│   └── fetch_posts.py          ← Instagram API fetcher
├── docs/                       ← GitHub Pages root
│   ├── index.html              ← the gallery page (edit this for design changes)
│   ├── posts.json              ← generated — do not edit manually
│   ├── CNAME                   ← custom domain
│   └── images/
│       └── *.jpg               ← downloaded thumbnails (auto-committed)
├── .gitignore
└── README.md
```

---

## Token refresh

Instagram long-lived tokens expire after **60 days** but can be refreshed anytime.
The script refreshes the token on every daily run and automatically updates the
`INSTAGRAM_ACCESS_TOKEN` GitHub Actions secret via the `gh` CLI.

The workflow has `secrets: write` permission for exactly this reason.

---

## Design changes

Edit `docs/index.html` directly — it's a self-contained HTML/CSS/JS file.
The Python script only touches `posts.json` and `images/`, so you can update
the design any time without touching the automation.
