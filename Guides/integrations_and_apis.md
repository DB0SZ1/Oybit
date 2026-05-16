# Oybit — Integrations & APIs

> Every external integration, every valid endpoint, every auth requirement. Scoped to 4 accounts across 3 platforms.

---

## Meta (Instagram Personal + Instagram Brand + Facebook)

All three accounts run through a single Facebook Developer App using the Meta Graph API. One app, three connected accounts.

**Base URL:** `https://graph.facebook.com/v19.0`

**App setup requirements:**
- Facebook Developer App with Instagram Graph API access
- Both Instagram accounts must be Business or Creator accounts (not personal)
- Both Instagram accounts must be linked to a Facebook Page
- Long-lived access tokens (60-day expiry, refreshed proactively by `token_refresher.py`)

**Required permissions:**
```
instagram_basic
instagram_content_publish
instagram_manage_comments
instagram_manage_insights
pages_manage_posts
pages_read_engagement
pages_show_list
publish_video
```

---

### Instagram — Publishing

**Single image post:**
```
POST /{ig-user-id}/media
  params:
    image_url=<url>
    caption=<text>
    access_token=<token>

POST /{ig-user-id}/media_publish
  params:
    creation_id=<container_id>
    access_token=<token>
```

**Carousel post:**
```
# Step 1 — Create each carousel item
POST /{ig-user-id}/media
  params:
    image_url=<url>
    is_carousel_item=true
    access_token=<token>
  → returns child_container_id (repeat for each slide)

# Step 2 — Create carousel container
POST /{ig-user-id}/media
  params:
    media_type=CAROUSEL
    children=<child_id_1,child_id_2,...>
    caption=<text>
    access_token=<token>

# Step 3 — Publish
POST /{ig-user-id}/media_publish
  params:
    creation_id=<carousel_container_id>
    access_token=<token>
```

**Reel (video):**
```
POST /{ig-user-id}/media
  params:
    media_type=REELS
    video_url=<url>
    caption=<text>
    share_to_feed=true
    access_token=<token>

# Poll until VIDEO_READY
GET /{container-id}?fields=status_code&access_token=<token>

POST /{ig-user-id}/media_publish
  params:
    creation_id=<container_id>
    access_token=<token>
```

**Story (photo):**
```
POST /{ig-user-id}/media
  params:
    image_url=<url>
    media_type=STORIES
    access_token=<token>

POST /{ig-user-id}/media_publish
  params:
    creation_id=<container_id>
    access_token=<token>
```

---

### Instagram — Analytics

```
GET /{ig-media-id}/insights
  params:
    metric=reach,impressions,likes,comments,shares,saved,follows
    access_token=<token>

GET /{ig-user-id}/insights
  params:
    metric=follower_count,impressions,reach,profile_views
    period=day|week|month
    access_token=<token>

GET /{ig-user-id}/media
  params:
    fields=id,caption,media_type,timestamp,like_count,comments_count
    access_token=<token>
```

---

### Instagram — Comments & Replies

```
GET /{ig-media-id}/comments
  params:
    fields=id,text,username,timestamp
    access_token=<token>

POST /{ig-comment-id}/replies
  params:
    message=<reply_text>
    access_token=<token>

DELETE /{ig-comment-id}
  params:
    access_token=<token>
```

---

### Facebook — Publishing

```
# Text post
POST /{page-id}/feed
  params:
    message=<text>
    access_token=<page_token>

# Photo post
POST /{page-id}/photos
  params:
    url=<image_url>
    caption=<text>
    access_token=<page_token>

# Video post
POST /{page-id}/videos
  params:
    file_url=<video_url>
    description=<text>
    title=<title>
    access_token=<page_token>
```

---

### Facebook — Analytics

```
GET /{page-id}/insights
  params:
    metric=page_impressions,page_reach,page_fans,page_views_total,
           page_post_engagements
    period=day|week|month|lifetime
    access_token=<page_token>

GET /{post-id}/insights
  params:
    metric=post_impressions,post_reach,post_reactions_by_type_total,
           post_clicks,post_shares
    access_token=<page_token>
```

---

### Facebook — Comments & Replies

```
GET /{post-id}/comments
  params:
    fields=id,message,from,created_time
    access_token=<page_token>

POST /{comment-id}/comments
  params:
    message=<reply_text>
    access_token=<page_token>

DELETE /{comment-id}
  params:
    access_token=<page_token>
```

---

## LinkedIn

**Base URL:** `https://api.linkedin.com/v2`

**Auth:** OAuth 2.0. Access token from LinkedIn OAuth flow. Stored encrypted in token store, refreshed before expiry.

**Required scopes:**
```
w_member_social
r_liteprofile
r_emailaddress
```

**Ahmad's person URN:** `urn:li:person:{person-id}` — retrieved once at setup via `GET /v2/me`.

---

### LinkedIn — Publishing (Text Post)

```
POST /v2/ugcPosts
Content-Type: application/json
Authorization: Bearer {access_token}

{
  "author": "urn:li:person:{id}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {
        "text": "<post_text>"
      },
      "shareMediaCategory": "NONE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

---

### LinkedIn — Publishing (Image Post)

```
# Step 1 — Register image upload
POST /v2/assets?action=registerUpload
{
  "registerUploadRequest": {
    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
    "owner": "urn:li:person:{id}",
    "serviceRelationships": [{
      "relationshipType": "OWNER",
      "identifier": "urn:li:userGeneratedContent"
    }]
  }
}
→ returns uploadUrl + asset URN

# Step 2 — Upload binary
PUT {uploadUrl}
  headers: Authorization: Bearer {token}
  body: image binary

# Step 3 — Create post with image
POST /v2/ugcPosts
{
  "author": "urn:li:person:{id}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": { "text": "<text>" },
      "shareMediaCategory": "IMAGE",
      "media": [{
        "status": "READY",
        "description": { "text": "<alt>" },
        "media": "<asset_urn>",
        "title": { "text": "<title>" }
      }]
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

---

### LinkedIn — Analytics

```
GET /v2/socialActions/{post-urn}
  → returns: likesSummary, commentsSummary

GET /v2/organizationalEntityShareStatistics
  params:
    q=organizationalEntity
    organizationalEntity=urn:li:person:{id}
    timeIntervals.timeGranularityType=DAY
    timeIntervals.timeRange.start={epoch_ms}
    timeIntervals.timeRange.end={epoch_ms}
```

---

### LinkedIn — Comments & Replies

```
GET /v2/socialActions/{post-urn}/comments

POST /v2/socialActions/{post-urn}/comments
{
  "actor": "urn:li:person:{id}",
  "message": { "text": "<reply_text>" }
}
```

---

## OpenRouter (Content Generation)

**Base URL:** `https://openrouter.ai/api/v1`

```python
POST /chat/completions
headers:
  Authorization: Bearer {OPENROUTER_API_KEY}
  HTTP-Referer: https://oybit.nyvora.com
  X-Title: Oybit

body:
{
  "model": "meta-llama/llama-4-scout",        # speed
  # or "anthropic/claude-sonnet-4-5"           # depth
  "messages": [
    {"role": "system", "content": "{persona_prompt}"},
    {"role": "user", "content": "{generation_brief}"}
  ],
  "temperature": 0.8,
  "max_tokens": 1000
}
```

---

## Pollinations.ai (Image Generation)

Free. No API key. No account. Direct HTTP call.

```python
import requests
from urllib.parse import quote

def generate_image(prompt: str, width=1080, height=1080) -> str:
    encoded = quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}"
    params = {
        "width": width,
        "height": height,
        "nologo": "true",
        "enhance": "true",
        "model": "flux"          # flux model gives best results
    }
    response = requests.get(url, params=params)
    # Returns image binary directly
    return url  # or save binary to disk
```

---

## Playwright (Carousel Rendering)

Runs on Railway server. Zero external cost.

```python
from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader
import asyncio

async def render_carousel_slide(
    template_name: str,
    context: dict,
    output_path: str
) -> str:
    # Render HTML from Jinja2 template
    env = Environment(loader=FileSystemLoader("render_engine/templates"))
    template = env.get_template(template_name)
    html = template.render(**context)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080}
        )
        await page.set_content(html, wait_until="networkidle")
        await page.screenshot(
            path=output_path,
            type="jpeg",
            quality=95,
            full_page=False
        )
        await browser.close()

    return output_path
```

---

## Remotion (Video Generation)

Runs on Railway server. Zero external cost.

**Node.js render command called from Python:**
```python
import subprocess
import json

def render_remotion_video(
    composition_id: str,   # e.g. "PersonalBrand" or "NyvoraBrand"
    props: dict,           # content, colors, fonts, timing
    output_path: str
) -> str:
    props_json = json.dumps(props)
    result = subprocess.run([
        "npx", "remotion", "render",
        f"src/index.tsx",
        composition_id,
        output_path,
        "--props", props_json,
        "--codec", "h264",
        "--image-format", "jpeg"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Remotion render failed: {result.stderr}")

    return output_path
```

**ffmpeg post-processing for platform compliance:**
```python
import subprocess

def process_for_instagram_reel(input_path: str, output_path: str) -> str:
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-vf", "scale=1080:1920,setsar=1",   # 9:16 aspect ratio
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ], check=True)
    return output_path
```

---

## MiroFish (Intelligence Layer)

MiroFish runs as a local module within the backend. No external API — it uses:
- **GraphRAG** via local Python implementation
- **OASIS** (pip install oasis-social) for simulation
- **Zep Cloud** for agent memory (free tier available)

```python
# Zep Cloud — agent memory
ZEP_API_KEY=<from_zep_cloud>

pip install graphrag
pip install oasis-social
pip install zep-cloud
```

**Seed ingestion (RSS + trends):**
```python
import feedparser
from pytrends.request import TrendReq

def collect_seeds(niche_keywords: list) -> list:
    feeds = [
        "https://techcrunch.com/feed/",
        "https://www.reddit.com/r/entrepreneur/.rss",
        "https://www.reddit.com/r/webdev/.rss",
        "https://www.reddit.com/r/SideProject/.rss",
        "https://news.ycombinator.com/rss",
    ]
    documents = []
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:
            documents.append({
                "title": entry.title,
                "content": entry.summary,
                "url": entry.link,
                "published": entry.published
            })

    pytrends = TrendReq()
    pytrends.build_payload(niche_keywords, timeframe="now 1-d")
    trending = pytrends.interest_over_time()
    # Add trending signals to documents

    return documents
```

---

## Portfolio Blog Integration

Ahmad's existing portfolio blog exposes an API. Oybit connects via:

```python
# Webhook receiver — called when blog publishes new post
POST /api/blog/webhook
{
  "event": "post_published",
  "post": {
    "title": "<title>",
    "content": "<full_markdown_content>",
    "url": "<post_url>",
    "tags": ["<tag1>", "<tag2>"]
  }
}
```

Or polling mode (if no webhook available):
```python
GET {BLOG_API_URL}/posts?since={last_check_timestamp}
Authorization: Bearer {BLOG_API_KEY}
```

`repurposer.py` then generates platform-native content from the post content automatically.

---

## Token Management

All tokens stored encrypted in PostgreSQL. `token_refresher.py` runs every 2 hours:

```python
# Meta token refresh (long-lived tokens expire in 60 days)
GET /oauth/access_token
  params:
    grant_type=fb_exchange_token
    client_id={APP_ID}
    client_secret={APP_SECRET}
    fb_exchange_token={current_token}

# LinkedIn token refresh
POST https://www.linkedin.com/oauth/v2/accessToken
  params:
    grant_type=refresh_token
    refresh_token={refresh_token}
    client_id={CLIENT_ID}
    client_secret={CLIENT_SECRET}
```

Tokens refreshed proactively when within 7 days of expiry. If refresh fails, Ahmad is notified via dashboard alert.
