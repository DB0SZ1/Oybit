# Oybit — Gap Solutions Master Document

> Every identified gap from brainstorming sessions, with concrete solutions. This is the instruction set for agents building Oybit. Read this alongside all 8 core docs. Every solution here overrides or extends what the core docs say where there is a conflict.

---

## How to Read This Document

Each gap is written as:
- **The Problem** — what breaks or is missing
- **The Solution** — exactly what to build and how
- **Where it lives** — which file/module/worker handles it

---

# PART 1 — API & PAYLOAD ARCHITECTURE

---

## GAP 1.1 — Image + Text Simultaneous Posting (Different API Structure Per Platform)

**The Problem:**
The publishers treat text and image as separate flows. Every platform uses a completely different API payload structure when you combine text AND image. Getting this wrong silently produces text-only posts or image-only posts with no error.

**The Solution:**

Add a `post_type` enum to every Post record and every publisher. Each publisher has a dedicated payload builder per type.

```python
# backend/publishers/post_types.py
from enum import Enum

class PostType(Enum):
    TEXT_ONLY = "text_only"
    IMAGE_ONLY = "image_only"
    TEXT_WITH_IMAGE = "text_with_image"
    TEXT_WITH_VIDEO = "text_with_video"
    CAROUSEL = "carousel"
    REEL = "reel"
    STORY = "story"
    REEL_WITH_CAPTION = "reel_with_caption"
```

**LinkedIn — text + image together (correct payload):**
```python
# Step 1: register upload → get asset URN
# Step 2: upload binary
# Step 3: ugcPost with BOTH commentary text AND media array populated
{
  "author": "urn:li:person:{id}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": { "text": "<post_text>" },    # ← BOTH must be present
      "shareMediaCategory": "IMAGE",
      "media": [{
        "status": "READY",
        "media": "<asset_urn>",
        "title": { "text": "<title>" }
      }]
    }
  },
  "visibility": { "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC" }
}
```

**Facebook — text + photo together (correct endpoint):**
```python
# NOT /photos with caption. NOT /feed with just message.
# Use /feed with attached_media array:

# Step 1: create unpublished photo objects
POST /{page-id}/photos
  params: url=<image_url>, published=false
  → returns photo_id

# Step 2: attach to feed post
POST /{page-id}/feed
  params:
    message=<text>
    attached_media=[{"media_fbid": "<photo_id>"}]
    access_token=<page_token>
```

**Facebook — multiple images + text:**
```python
# Create all photo objects unpublished first, then one /feed call
photo_ids = []
for image_url in image_urls:
    r = POST /{page-id}/photos params={url: image_url, published: false}
    photo_ids.append(r["id"])

POST /{page-id}/feed
  params:
    message=<text>
    attached_media=[{"media_fbid": pid} for pid in photo_ids]
```

**Where it lives:** Each publisher file (`linkedin.py`, `facebook.py`, `instagram_personal.py`, `instagram_brand.py`) must implement `build_payload(post_type: PostType, content: dict) -> dict` as its first function. `dispatcher.py` always passes `post_type` explicitly.

---

## GAP 1.2 — Meta Graph API Error Handling (Non-Standard Error Format)

**The Problem:**
Meta returns HTTP 200 with an error JSON body when tokens expire (error code 190). Standard HTTP error handling misses this completely. The publisher logs "success" while the post never went live.

**The Solution:**
```python
# backend/publishers/meta_error_handler.py

def check_meta_response(response: dict, account: str) -> None:
    """Always call this after every Meta API response."""
    if "error" in response:
        error = response["error"]
        code = error.get("code")
        subcode = error.get("error_subcode")

        if code == 190:
            raise TokenExpiredError(account=account, subcode=subcode)
        elif code == 32 or code == 17:
            raise RateLimitError(account=account, retry_after=300)
        elif code == 10:
            raise PermissionError(account=account, message=error.get("message"))
        elif code == 368:
            raise AccountBlockedError(account=account)
        else:
            raise MetaAPIError(code=code, message=error.get("message"), account=account)
```

Every Meta API call in every publisher must pipe its response through `check_meta_response()` before any success logic runs.

---

## GAP 1.3 — LinkedIn 422 Error Handling

**The Problem:**
LinkedIn returns 422 (not 400) for malformed `ugcPosts` payloads. Agents might handle 4xx generically and miss the specific cause, making debugging impossible.

**The Solution:**
```python
# In linkedin.py — dedicated LinkedIn error handler

def handle_linkedin_error(response: requests.Response, payload: dict) -> None:
    if response.status_code == 422:
        body = response.json()
        logger.error(
            "LinkedIn 422 — malformed payload",
            extra={
                "status": 422,
                "error_body": body,
                "payload_sent": payload,  # log the exact payload for debugging
                "module": "linkedin.publisher"
            }
        )
        raise LinkedInPayloadError(body=body, payload=payload)
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise LinkedInRateLimitError(retry_after=retry_after)
    elif response.status_code == 401:
        raise LinkedInTokenError()
```

---

## GAP 1.4 — OpenRouter 429 with Retry-After Header

**The Problem:**
OpenRouter returns 429 with a `Retry-After` header. If the generator just sleeps a fixed time instead of reading that header, it either waits too long (wasting time) or too short (getting rate limited again).

**The Solution:**
```python
# backend/content/generator.py — OpenRouter call wrapper

import time

def call_openrouter(payload: dict, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 30))
            logger.warning(f"OpenRouter 429 — waiting {retry_after}s", extra={"attempt": attempt})
            time.sleep(retry_after)
            continue

        if response.status_code != 200:
            raise OpenRouterError(status=response.status_code, body=response.text)

        return response.json()

    raise OpenRouterMaxRetriesError(attempts=max_retries)
```

---

## GAP 1.5 — Pollinations.ai Content-Type Check

**The Problem:**
Pollinations.ai sometimes returns an HTML error page instead of an image. `image.py` saves it as a .jpg and the post goes out with a corrupt image file.

**The Solution:**
```python
# backend/render_engine/image.py

def download_pollinations_image(url: str, output_path: str) -> str:
    response = requests.get(url, timeout=30)

    content_type = response.headers.get("Content-Type", "")
    if "image" not in content_type:
        logger.error(
            "Pollinations returned non-image content",
            extra={"content_type": content_type, "url": url, "body_preview": response.text[:200]}
        )
        raise PollinationsImageError(content_type=content_type)

    if len(response.content) < 1000:  # suspiciously small — probably an error
        raise PollinationsImageError(message="Response too small to be a real image")

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path
```

---

# PART 2 — COMMUNITY & GROWTH MODULES (MISSING ENTIRELY)

---

## GAP 2.1 — Facebook Groups Posting (Ahmad's Personal Account)

**The Problem:**
Facebook page organic reach is 2–5%. Real organic growth on Facebook happens through Groups. But Nyvora page cannot post in most groups — only personal accounts can. This module is entirely absent.

**The Solution:**

Add `facebook_personal.py` publisher and a `group_strategy.py` module.

```
backend/publishers/
  └── facebook_personal.py    ← NEW — Ahmad's personal Facebook account

backend/intelligence/
  └── group_strategy.py       ← NEW — which groups, when, what to post
```

**Group post endpoint:**
```python
# facebook_personal.py

def post_to_group(group_id: str, message: str, access_token: str) -> str:
    """
    Requires: Ahmad's personal user access token (NOT page token)
    Requires: Ahmad is a member of the group
    Requires: publish_to_groups permission in Facebook App
    """
    url = f"https://graph.facebook.com/v19.0/{group_id}/feed"
    payload = {"message": message, "access_token": access_token}
    response = requests.post(url, data=payload)
    check_meta_response(response.json(), "facebook_personal")
    return response.json()["id"]
```

**Group list config (stored in DB, not hardcoded):**
```python
# backend/db/models.py — add FacebookGroup model

class FacebookGroup(Base):
    __tablename__ = "facebook_groups"
    id = Column(String, primary_key=True)        # group_id from Meta
    name = Column(String)
    niche_relevance = Column(Float)              # 0-1, how relevant to Ahmad's niche
    posting_frequency_days = Column(Integer)    # min days between posts in this group
    last_posted_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    requires_approval = Column(Boolean)         # some groups moderate posts
```

**What Ahmad needs to do manually:** Join the groups first. Oybit cannot join groups via API.

---

## GAP 2.2 — LinkedIn Groups Posting

**The Problem:**
LinkedIn Groups have 10x+ organic reach compared to personal feed posts for niche content. Zero mention in any Oybit doc.

**The Solution:**

Add group posting to `linkedin.py` as a new post type.

```python
# linkedin.py — add group post method

def post_to_linkedin_group(group_urn: str, text: str, access_token: str) -> str:
    """
    group_urn format: urn:li:group:{group_id}
    containerEntity in ugcPost payload must be set to group URN
    """
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "containerEntity": group_urn,   # ← this is what makes it a group post
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    # ... post to /v2/ugcPosts
```

**Group list stored same way as Facebook groups.** Ahmad joins groups manually; Oybit posts to them on a cadence.

---

## GAP 2.3 — Reddit Comment Strategy (Not Just Posts)

**The Problem:**
Reddit reputation is built through comments, not just posts. Commenting genuine value on hot posts in target subreddits (r/webdev, r/SideProject, r/entrepreneur, r/nigeria) drives profile visits and follows. This is completely absent.

**The Solution:**

Add `reddit_commenter.py` module.

```
backend/publishers/
  └── reddit_commenter.py     ← NEW

backend/intelligence/
  └── reddit_opportunity.py   ← NEW — finds comment-worthy posts
```

```python
# backend/intelligence/reddit_opportunity.py

import praw

def find_comment_opportunities(subreddits: list, keywords: list) -> list:
    """
    Finds hot posts in target subreddits where Ahmad can add genuine value.
    Returns list of opportunities for approval queue.
    """
    reddit = praw.Reddit(...)
    opportunities = []

    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.hot(limit=20):
            # Only comment on posts < 6 hours old (still getting traffic)
            if post.created_utc < (time.time() - 21600):
                continue
            # Only if Ahmad hasn't already commented
            if already_commented(post.id):
                continue
            # Only if topic is relevant
            relevance = compute_relevance(post.title + post.selftext, keywords)
            if relevance > 0.6:
                opportunities.append({
                    "post_id": post.id,
                    "title": post.title,
                    "url": post.url,
                    "subreddit": subreddit_name,
                    "score": post.score,
                    "relevance": relevance
                })

    return opportunities
```

```python
# backend/publishers/reddit_commenter.py

def post_comment(post_id: str, comment_text: str) -> str:
    """
    Add a human-timing delay before posting (Reddit shadowbans bot-speed posting)
    """
    import random
    time.sleep(random.uniform(30, 120))  # 30s–2min human-like delay

    submission = reddit.submission(id=post_id)
    comment = submission.reply(comment_text)
    return comment.id
```

Comments go through the approval queue — Ahmad always approves before a comment is posted. Never automated. Comments must be genuine value, never promotional.

---

## GAP 2.4 — Comment Opportunity Module (Commenting on Others' Posts for Growth)

**The Problem:**
The most powerful LinkedIn and Instagram growth tactic is being the first thoughtful comment on a high-follower account's post. This exposes Ahmad to thousands of new accounts. Zero mention in any doc.

**The Solution:**

Add `comment_opportunity.py` to the intelligence layer.

```
backend/intelligence/
  └── comment_opportunity.py   ← NEW
```

```python
# backend/intelligence/comment_opportunity.py

def find_linkedin_comment_opportunities() -> list:
    """
    Monitor recent posts from target accounts in Ahmad's niche.
    Surface posts where a comment from Ahmad would be visible to large audiences.
    """
    target_accounts = get_niche_accounts_to_monitor()  # stored in DB
    opportunities = []

    for account_urn in target_accounts:
        # GET /v2/ugcPosts?q=authors&authors=<urn>
        recent_posts = fetch_linkedin_posts(account_urn, limit=5)

        for post in recent_posts:
            age_hours = (datetime.now() - post.created_at).total_seconds() / 3600
            if age_hours > 2:  # only post when still fresh
                continue
            if post.comment_count < 10:  # too early, not enough traction yet
                continue
            if post.comment_count > 200:  # too late, buried
                continue
            opportunities.append({
                "post_urn": post.urn,
                "author": post.author,
                "text_preview": post.text[:200],
                "comment_count": post.comment_count,
                "estimated_reach": post.author_followers * 0.1
            })

    return opportunities
```

These are served in the dashboard as "Comment Opportunities." Ahmad clicks, sees the post, sees a drafted comment in his voice, edits if needed, approves. Never fully automated.

---

## GAP 2.5 — LinkedIn Newsletter

**The Problem:**
LinkedIn Newsletters push to all subscribers as notifications — 10x the reach of regular posts. Not mentioned anywhere in any doc.

**The Solution:**

Add `linkedin_newsletter.py` publisher.

```python
# backend/publishers/linkedin_newsletter.py

def publish_newsletter_article(title: str, content_html: str, access_token: str) -> str:
    """
    LinkedIn article via /v2/articles
    Requires: w_member_social scope
    Newsletter must be created once manually in LinkedIn UI first
    """
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "title": {"text": title},
        "content": {"contentEntities": [{"entityLocation": "..."}]},
        "subject": {"text": title},
        "coverImage": {...}  # optional
    }
    # POST /v2/articles
```

Weekly newsletter cadence — Sunday evening WAT. Generated by `bulk.py` from the week's best content and learnings. Goes through approval queue always.

---

## GAP 2.6 — Instagram Collab Posts

**The Problem:**
Instagram Collab posts appear on both accounts' feeds simultaneously — the only free way to cross-pollinate audiences between Ahmad's personal IG and Nyvora brand IG.

**The Solution:**
```python
# instagram_personal.py OR instagram_brand.py — add collab method

def create_collab_post(primary_ig_user_id: str, collaborator_ig_user_id: str,
                       image_url: str, caption: str, access_token: str) -> str:
    """
    collaboration_tagged_user_ids in media creation
    Collaborator must accept the invite via the IG app (cannot be automated)
    """
    payload = {
        "image_url": image_url,
        "caption": caption,
        "collaboration_tagged_user_ids": [collaborator_ig_user_id],
        "access_token": access_token
    }
    # POST /{ig-user-id}/media
```

Collab posts are generated once per week maximum. Both accounts must be controlled by Ahmad so the accept step is manual but quick.

---

# PART 3 — MISSING PUBLISHERS

---

## GAP 3.1 — Pinterest Publisher (Completely Absent)

**The Problem:**
Pinterest was listed as a platform in architecture but `pinterest.py` was never built.

**The Solution:**

```
backend/publishers/
  └── pinterest.py           ← NEW
```

```python
# backend/publishers/pinterest.py
# Uses Pinterest API v5

import requests

PINTEREST_API = "https://api.pinterest.com/v5"

def create_pin(board_id: str, title: str, description: str,
               image_url: str, link: str, access_token: str) -> str:
    """
    Pinterest SEO strategy: keyword-rich title + description.
    Pin lives forever in search results — not ephemeral like other platforms.
    """
    payload = {
        "board_id": board_id,
        "title": title,                      # keyword-rich, max 100 chars
        "description": description,          # keyword-rich, max 800 chars
        "media_source": {
            "source_type": "image_url",
            "url": image_url                 # 2:3 ratio optimal (1000x1500px)
        },
        "link": link                         # Ahmad's portfolio or product link
    }
    response = requests.post(
        f"{PINTEREST_API}/pins",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json()["id"]
```

**Pinterest-specific rules:**
- Optimal image size: 1000×1500px (2:3 ratio) — add this to render_engine
- Posting cadence: 5–10 pins/day (far more than other platforms — use bulk mode)
- Board structure: one board per content pillar (Building in Public, African Tech, Security & Dev, Nyvora Products)
- Rich Pins (for blog posts): require domain verification in Pinterest settings — do once manually
- Pinterest SEO = hashtags are dead on Pinterest — keywords in title/description are everything

---

## GAP 3.2 — YouTube Publisher (Listed, Not Built)

**The Problem:**
YouTube Data API v3 was listed but `youtube.py` was never built.

**The Solution:**

```
backend/publishers/
  └── youtube.py             ← NEW
```

```python
# backend/publishers/youtube.py
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_youtube_video(video_path: str, title: str, description: str,
                          tags: list, is_short: bool = False) -> str:
    youtube = build("youtube", "v3", credentials=get_oauth_credentials())

    if is_short:
        title = f"{title} #Shorts"  # required for Shorts classification
        # Ensure video is 9:16 aspect ratio and < 60 seconds (handled by render engine)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28"  # Science & Technology
        },
        "status": {"privacyStatus": "public"}
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()

    video_id = response["id"]

    # Upload thumbnail separately (requires channel verification)
    if thumbnail_path:
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path))

    return video_id

def post_community_update(text: str) -> str:
    """YouTube Community posts — text updates to subscribers"""
    # POST to YouTube Data API community posts endpoint
    # Good for between-video engagement
    pass
```

**YouTube-specific rules:**
- Shorts: 9:16 ratio, under 60s, `#Shorts` in title — Remotion must output this format
- Thumbnail is uploaded separately after video — needs `thumbnail.jpg` generated by render engine
- YouTube OAuth is separate from Meta and LinkedIn — add `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` to env vars

---

## GAP 3.3 — Bluesky Rich Text Facets (Currently Broken)

**The Problem:**
Bluesky AT Protocol requires explicit `facets` in the record structure for links, mentions, and hashtags to be clickable. A plain text post with a URL is just text — not a link. Both agents almost certainly got this wrong.

**The Solution:**
```python
# backend/publishers/bluesky.py (add facet builder)

from atproto import Client, models

def build_facets(text: str) -> list:
    """
    Parse text and build facets for URLs, mentions, and hashtags.
    Without this, #hashtags and URLs don't work on Bluesky.
    """
    import re
    facets = []

    # URLs
    for match in re.finditer(r"https?://\S+", text):
        facets.append({
            "$type": "app.bsky.richtext.facet",
            "index": {
                "byteStart": len(text[:match.start()].encode("utf-8")),
                "byteEnd": len(text[:match.end()].encode("utf-8"))
            },
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": match.group()}]
        })

    # Hashtags
    for match in re.finditer(r"#(\w+)", text):
        facets.append({
            "$type": "app.bsky.richtext.facet",
            "index": {
                "byteStart": len(text[:match.start()].encode("utf-8")),
                "byteEnd": len(text[:match.end()].encode("utf-8"))
            },
            "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": match.group(1)}]
        })

    return facets

def post_to_bluesky(text: str, image_path: str = None) -> str:
    client = Client()
    client.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)

    # Images: upload blob first, then reference
    images = []
    if image_path:
        with open(image_path, "rb") as f:
            blob_response = client.upload_blob(f.read())
        images = [models.AppBskyEmbedImages.Image(image=blob_response.blob, alt="")]

    record = {
        "text": text,
        "facets": build_facets(text),   # ← critical — without this nothing is clickable
        "embed": models.AppBskyEmbedImages.Main(images=images) if images else None
    }
    response = client.post(record)
    return response.uri
```

---

# PART 4 — RENDERING ENGINE GAPS

---

## GAP 4.1 — Playwright System Dependencies on Railway/Render

**The Problem:**
Playwright needs `libX11`, `libXcomposite`, `libXdamage`, `libXext`, `libXrandr`, `libGbm`, `libasound2` — none of which are installed by default on Railway or Render. Carousel rendering silently fails with a cryptic "browser not found" error.

**The Solution:**

`railway.toml` must specify Nixpacks config, OR use a Dockerfile:

```dockerfile
# Dockerfile (use this if Nixpacks doesn't resolve the deps)
FROM python:3.11-slim

# System deps for Playwright + Remotion
RUN apt-get update && apt-get install -y \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 \
    libxss1 libxtst6 libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 \
    libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    nodejs npm \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt
RUN playwright install chromium --with-deps
```

Add to `nixpacks.toml` for Railway Nixpacks path:
```toml
[phases.setup]
nixPkgs = ["chromium", "ffmpeg", "nodejs_20", "playwright-driver"]

[phases.install]
cmds = ["pip install -r requirements.txt", "playwright install chromium"]
```

---

## GAP 4.2 — Remotion on Railway/Render (Node.js + Python Same Service)

**The Problem:**
Remotion uses Puppeteer/Chrome internally — same missing system deps as Playwright. Additionally, Node.js must be available alongside Python in the same Railway service. The Dockerfile above handles both. But the subprocess call needs validation.

**The Solution:**
```python
# backend/render_engine/video.py — add output validation

def render_remotion_video(composition_id: str, props: dict, output_path: str) -> str:
    result = subprocess.run(
        ["npx", "remotion", "render", "src/index.tsx", composition_id, output_path,
         "--props", json.dumps(props), "--codec", "h264"],
        capture_output=True, text=True, timeout=600
    )

    # DO NOT trust returncode alone — Remotion can exit 0 with no output
    if not os.path.exists(output_path):
        logger.error(
            "Remotion render: process exited but output file missing",
            extra={"returncode": result.returncode, "stderr": result.stderr, "stdout": result.stdout}
        )
        raise RemoionRenderError(f"Output file not created: {output_path}")

    file_size = os.path.getsize(output_path)
    if file_size < 10000:  # < 10KB is definitely corrupt
        raise RemotionRenderError(f"Output file suspiciously small: {file_size} bytes")

    return output_path
```

---

## GAP 4.3 — Font Availability in Playwright Renders

**The Problem:**
If `persona.md` specifies a Google Font (e.g. Bricolage Grotesque), Playwright's headless Chromium won't have it unless explicitly loaded. Renders use system fallback fonts and look wrong.

**The Solution:**
All carousel HTML templates must load fonts via `@import` at the top of the `<style>` block, not assume system availability:

```html
<!-- render_engine/templates/carousel_base.html -->
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;800&display=swap');
  /* or use font-face with base64 embedded font for offline Railway rendering */

  :root {
    --font-primary: '{{ persona.font_primary }}', sans-serif;
    --font-secondary: '{{ persona.font_secondary }}', sans-serif;
    --color-primary: {{ persona.color_primary }};
    --color-accent: {{ persona.color_accent }};
  }
</style>
```

For fully offline rendering (no network call during render), embed fonts as base64 in the template. Add a `font_embedder.py` utility that converts Google Font URLs to base64 data URIs on first run and caches them.

---

## GAP 4.4 — Carousel Slide Text Overflow Validation

**The Problem:**
If generated text is too long for a slide, Playwright renders it cut off with no error. Posts go out with broken carousels.

**The Solution:**
```python
# backend/render_engine/carousel.py — add pre-render validation

MAX_CHARS_PER_SLIDE = {
    "headline": 60,
    "body": 180,
    "caption": 120
}

def validate_slide_content(slides: list) -> list:
    errors = []
    for i, slide in enumerate(slides):
        for field, max_chars in MAX_CHARS_PER_SLIDE.items():
            content = slide.get(field, "")
            if len(content) > max_chars:
                errors.append(f"Slide {i+1} {field}: {len(content)} chars > max {max_chars}")

    if errors:
        raise SlideContentOverflowError(errors=errors)
    return slides
```

This runs BEFORE `render_carousel_slide()` is called. Errors go back to the generator with a specific "shorten slide X body text" instruction.

---

## GAP 4.5 — Video Pre-Upload Validation for Instagram

**The Problem:**
Instagram Reels max file size 1GB, max duration 90s, min duration 3s. A valid MP4 can be rejected by Instagram silently.

**The Solution:**
```python
# backend/render_engine/video.py — add pre-upload validator

import subprocess, json

def validate_video_for_instagram(video_path: str) -> None:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
         "-show_streams", video_path],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)

    duration = float(data["format"]["duration"])
    size_bytes = int(data["format"]["size"])

    if duration < 3:
        raise VideoValidationError(f"Too short: {duration}s (min 3s)")
    if duration > 90:
        raise VideoValidationError(f"Too long: {duration}s (max 90s for Reels)")
    if size_bytes > 1_000_000_000:
        raise VideoValidationError(f"Too large: {size_bytes} bytes (max 1GB)")

    # Check aspect ratio
    video_stream = next(s for s in data["streams"] if s["codec_type"] == "video")
    width, height = video_stream["width"], video_stream["height"]
    ratio = height / width
    if not (1.7 < ratio < 1.9):  # 9:16 = 1.778
        raise VideoValidationError(f"Wrong aspect ratio: {width}x{height} (need 9:16)")
```

---

## GAP 4.6 — Render Queue (Max 1 Concurrent Render)

**The Problem:**
If the scheduler triggers two carousel renders simultaneously, two headless Chrome instances compete for memory. Railway free tier will OOM.

**The Solution:**
```python
# backend/render_engine/render_queue.py

import asyncio

_render_semaphore = asyncio.Semaphore(1)  # max 1 render at a time

async def enqueue_render(render_fn, *args, **kwargs):
    async with _render_semaphore:
        return await render_fn(*args, **kwargs)
```

Every call to `carousel.py` and `video.py` must go through `enqueue_render()`.

---

# PART 5 — DATABASE & DATA INTEGRITY

---

## GAP 5.1 — Single `Base` Declaration (Critical Merge Risk)

**The Problem:**
Agent A and Agent B both likely wrote `Base = declarative_base()` in their respective model files. When merged, SQLAlchemy will have two Bases and relationship foreign keys between them will break.

**The Solution:**

One canonical location, imported everywhere:
```python
# backend/db/base.py — THE ONLY PLACE Base is defined
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# backend/db/models.py — imports from base.py
from backend.db.base import Base
```

First thing to verify after merge:
```bash
python -c "from backend.db.models import *; print('Models OK')"
python -c "from backend.main import app; print('App import OK')"
```

---

## GAP 5.2 — SQLite WAL Mode

**The Problem:**
SQLite default journal mode causes locking errors when `scheduler_worker` and `analytics_worker` both access `queue.db` simultaneously.

**The Solution:**
```python
# backend/scheduler_worker/queue.py — set WAL mode on connection

from sqlalchemy import create_engine, event

engine = create_engine(f"sqlite:///{QUEUE_DB_PATH}")

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()
```

---

## GAP 5.3 — Alembic Migration Conflict Resolution

**The Problem:**
If both agents ran `alembic revision --autogenerate` separately, there will be two migration heads that conflict. `alembic upgrade head` will fail.

**The Solution:**
```bash
# After merging both agents' code:
alembic heads  # will show 2 heads if conflict exists

# Merge them:
alembic merge -m "merge_agent_a_and_agent_b" <head_1> <head_2>
alembic upgrade head  # now has single merged head
```

Then add a startup check in `main.py`:
```python
# backend/main.py
from alembic import command
from alembic.config import Config

def check_migrations():
    alembic_cfg = Config("alembic.ini")
    # Will raise if DB is not at latest revision
    command.check(alembic_cfg)
```

---

## GAP 5.4 — persona.md Atomic Writes

**The Problem:**
If power cuts or process is killed during a `persona.md` write, the file is half-written and permanently corrupt.

**The Solution:**
```python
# backend/persona_engine/updater.py — always use atomic write

import os, tempfile

def write_persona_atomically(content: str, persona_path: str) -> None:
    """Write to temp file, then rename. Rename is atomic on Linux."""
    dir_name = os.path.dirname(persona_path)
    with tempfile.NamedTemporaryFile(mode="w", dir=dir_name,
                                     delete=False, suffix=".tmp") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    os.replace(tmp_path, persona_path)  # atomic on Linux — either succeeds or fails, never partial
    logger.info("persona.md written atomically", extra={"path": persona_path})
```

---

## GAP 5.5 — simulation_log.md File Locking

**The Problem:**
If `calibration.py` and `feedback_worker.py` both try to append to `simulation_log.md` simultaneously, file corruption is possible.

**The Solution:**
```python
# backend/persona_engine/updater.py — use file locking for simulation_log

import fcntl

def append_to_simulation_log(entry: str, log_path: str) -> None:
    with open(log_path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # exclusive lock — blocks until available
        try:
            f.write(entry + "\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
```

---

## GAP 5.6 — PostgreSQL Connection Pooling

**The Problem:**
FastAPI + SQLAlchemy without explicit connection pooling will exhaust DB connections under concurrent requests.

**The Solution:**
```python
# backend/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # max persistent connections
    max_overflow=10,      # max temporary connections above pool_size
    pool_pre_ping=True,   # test connections before use (handles Railway DB restarts)
    pool_recycle=3600     # recycle connections every hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

---

## GAP 5.7 — Data Retention & Archiving

**The Problem:**
PostAnalytics, MiroFishRun records, and simulation_log.md grow forever. After 1 year: thousands of rows, large JSON blobs, multi-MB log file.

**The Solution:**

Add archiving to `feedback_worker.py` (runs weekly):
```python
# backend/feedback_loop/archiver.py — NEW

def archive_old_analytics(cutoff_days: int = 180) -> int:
    """Move PostAnalytics older than cutoff to archive table."""
    cutoff = datetime.now() - timedelta(days=cutoff_days)
    old_records = session.query(PostAnalytics).filter(PostAnalytics.measured_at < cutoff).all()
    # Insert into PostAnalyticsArchive table (compressed JSON)
    # Delete from PostAnalytics
    return len(old_records)

def compress_old_mirofish_runs(cutoff_days: int = 90) -> int:
    """Compress MiroFishRun JSON blobs older than cutoff."""
    # Replace full JSON with compressed summary
    pass

def check_simulation_log_size(log_path: str) -> None:
    size_mb = os.path.getsize(log_path) / (1024 * 1024)
    if size_mb > 10:
        logger.warning("simulation_log.md exceeds 10MB", extra={"size_mb": size_mb})
        # Alert Ahmad via dashboard notification
```

---

# PART 6 — DEPLOYMENT & HOSTING

---

## GAP 6.1 — Render Anti-Sleep Self-Ping

**The Problem:**
Render free tier sleeps after 15 minutes of inactivity. A sleeping API means workers can't call internal endpoints and Ahmad can't access the dashboard.

**The Solution:**

Add a self-ping worker as a separate Render service:
```python
# workers/health_pinger.py — NEW

import requests, time, os

HEALTH_URL = os.environ["API_BASE_URL"] + "/health"
PING_INTERVAL = 600  # 10 minutes

def ping_forever():
    while True:
        try:
            r = requests.get(HEALTH_URL, timeout=10)
            logger.info("Health ping", extra={"status": r.status_code})
        except Exception as e:
            logger.warning("Health ping failed", extra={"error": str(e)})
        time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    ping_forever()
```

Add `render.yaml` (Render deployment config):
```yaml
services:
  - type: web
    name: oybit-api
    env: python
    buildCommand: pip install -r requirements.txt && playwright install chromium
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health

  - type: worker
    name: oybit-scheduler
    startCommand: python workers/scheduler_worker.py

  - type: worker
    name: oybit-health-pinger
    startCommand: python workers/health_pinger.py

  - type: worker
    name: oybit-mirofish
    startCommand: python workers/mirofish_worker.py

  - type: worker
    name: oybit-analytics
    startCommand: python workers/analytics_worker.py

  - type: worker
    name: oybit-feedback
    startCommand: python workers/feedback_worker.py

  - type: worker
    name: oybit-token-refresher
    startCommand: python workers/token_refresher.py

databases:
  - name: oybit-postgres
    plan: free

  - name: oybit-redis
    plan: free
```

---

## GAP 6.2 — Deep Health Endpoint

**The Problem:**
The current `/health` endpoint just returns `{"status": "ok"}`. Render and Railway will mark the service healthy even when the DB is down.

**The Solution:**
```python
# backend/api/health.py

from fastapi import APIRouter
import redis, sqlalchemy

router = APIRouter()

@router.get("/health")
async def health_check():
    checks = {}

    # DB check
    try:
        session.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"ERROR: {str(e)}"

    # Redis check
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"ERROR: {str(e)}"

    # Volume mount check (persona.md exists)
    persona_path = os.environ.get("PERSONA_PATH", "/data/personas/ahmad/persona.md")
    checks["volume"] = "ok" if os.path.exists(persona_path) else "ERROR: persona.md not found"

    # SQLite queue check
    queue_path = "/data/queue.db"
    checks["queue_db"] = "ok" if os.path.exists(queue_path) else "ERROR: queue.db not on disk"

    all_ok = all("ok" == v for v in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks
    }
```

---

## GAP 6.3 — SIGTERM Graceful Shutdown

**The Problem:**
Railway and Render both send SIGTERM before killing processes. If workers don't catch it, they corrupt the SQLite queue mid-write.

**The Solution:**
```python
# Every worker file — add SIGTERM handler

import signal, sys

def handle_sigterm(signum, frame):
    logger.info("SIGTERM received — shutting down gracefully")
    # Mark any running jobs back to pending
    reset_stale_running_jobs()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

def reset_stale_running_jobs():
    """On startup AND on shutdown: reset any 'running' jobs to 'pending'."""
    session.query(SchedulerJob).filter(
        SchedulerJob.status == "running"
    ).update({"status": "pending", "last_error": "Reset by SIGTERM handler"})
    session.commit()
```

Also call `reset_stale_running_jobs()` at the START of every worker — handles the crash-restart scenario.

---

## GAP 6.4 — Stale Running Jobs Cleanup on Startup

**The Problem:**
If `scheduler_worker` crashes mid-dispatch, the job stays as `running` forever and never retries.

**The Solution:**
Already covered in GAP 6.3 — call `reset_stale_running_jobs()` at startup of `scheduler_worker.py`. Additionally:

```python
# backend/scheduler_worker/queue.py

JOB_TIMEOUT_MINUTES = 30  # any job stuck in 'running' for 30+ min is assumed crashed

def cleanup_stale_jobs():
    cutoff = datetime.now() - timedelta(minutes=JOB_TIMEOUT_MINUTES)
    stale = session.query(SchedulerJob).filter(
        SchedulerJob.status == "running",
        SchedulerJob.updated_at < cutoff
    ).all()
    for job in stale:
        job.status = "pending"
        job.last_error = "Reset: exceeded timeout"
        logger.warning("Reset stale job", extra={"job_id": job.id})
    session.commit()
```

Run `cleanup_stale_jobs()` at startup and every 30 minutes.

---

## GAP 6.5 — Railway Volume Mount Verification

**The Problem:**
If the Railway Volume isn't mounted, SQLite creates an in-memory DB. Jobs survive restarts but disappear on redeploy with no error.

**The Solution:**
```python
# backend/main.py — startup check

def verify_volume_mounts():
    required_paths = [
        "/data/personas/ahmad",
        "/data",
    ]
    for path in required_paths:
        if not os.path.exists(path):
            logger.critical(f"Required volume path not found: {path}")
            raise RuntimeError(f"Volume not mounted at {path}. Check railway.toml volume configuration.")

    # Test write (not just existence)
    test_file = "/data/.write_test"
    try:
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
    except Exception as e:
        raise RuntimeError(f"Volume at /data is not writable: {e}")
```

Call this at FastAPI startup before the app begins accepting requests.

---

# PART 7 — ERROR HANDLING & LOGGING

---

## GAP 7.1 — Structured JSON Logging (All Modules)

**The Problem:**
Print statements don't work with Railway/Render log aggregation. Non-structured logs make debugging impossible.

**The Solution:**

One canonical logger, used everywhere:
```python
# backend/logger.py — shared structured logger

import logging, json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        # Merge any extra fields passed via extra={}
        if hasattr(record, "__dict__"):
            for key, val in record.__dict__.items():
                if key not in ("msg", "args", "levelname", "levelno", "pathname",
                               "filename", "module", "funcName", "created", "msecs",
                               "relativeCreated", "thread", "threadName", "processName",
                               "process", "message", "exc_info", "exc_text", "stack_info"):
                    log_entry[key] = val

        return json.dumps(log_entry)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

Usage in every module:
```python
from backend.logger import get_logger
logger = get_logger(__name__)

# Platform API call
logger.info("Publishing post", extra={
    "platform": "linkedin",
    "account": "ahmad_personal",
    "post_id": post.id,
    "post_type": post_type.value
})

# Error
logger.error("LinkedIn publish failed", extra={
    "platform": "linkedin",
    "status_code": response.status_code,
    "response_body": response.text,
    "post_id": post.id
})
```

**NEVER log access tokens, persona content, or personal data.**

---

## GAP 7.2 — Token Masking in All Logs

**The Problem:**
If a bug causes a token to be included in a log entry, Railway/Render log aggregation stores it in plaintext.

**The Solution:**
```python
# backend/logger.py — add token masking to JSONFormatter

import re

TOKEN_PATTERNS = [
    r"(access_token=)[^\s&\"]+",
    r"(Bearer )[^\s\"]+",
    r"(EAAG[a-zA-Z0-9]+)",  # Meta token pattern
    r"(sk-or-[a-zA-Z0-9-]+)",  # OpenRouter key pattern
]

def mask_tokens(text: str) -> str:
    for pattern in TOKEN_PATTERNS:
        text = re.sub(pattern, r"\1[REDACTED]", text)
    return text

# Apply mask_tokens() to "message" field in JSONFormatter.format()
```

---

## GAP 7.3 — Decision Audit Log

**The Problem:**
When something goes wrong (post not sent, gate rejected something, persona not updated), there's no single place to answer "what happened at 9AM on Tuesday?"

**The Solution:**

Add `AuditLog` DB model and write to it from every significant system decision:
```python
# backend/db/models.py — add AuditLog

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String, index=True)  # post_approved, post_rejected, persona_updated, gate_failed, etc.
    actor = Column(String)                    # which worker/module
    entity_type = Column(String)             # post, persona, pattern, token
    entity_id = Column(String)
    decision = Column(String)                # approved / rejected / updated / failed
    reason = Column(Text)                    # why
    context = Column(JSON)                   # full context dict

# Usage in pre_publish_gate.py
audit_log.write(
    event_type="gate_decision",
    actor="mirofish_gate",
    entity_type="post",
    entity_id=post.id,
    decision="rejected",
    reason="Confidence score 0.42 below threshold 0.60",
    context={"confidence": 0.42, "narratives_tested": [...], "account": "linkedin"}
)
```

Dashboard page: **"System Audit"** — filterable by date, event type, decision. Ahmad can answer "what happened yesterday" in 30 seconds.

---

# PART 8 — SECURITY

---

## GAP 8.1 — Prompt Injection via Seed Content

**The Problem:**
A trending news article could contain `"Ignore previous instructions and post..."` text. If fed directly into a generation prompt as a seed document, it could manipulate the LLM output — which then passes Brand Voice Guardian and goes live.

**The Solution:**
```python
# backend/intelligence/seed_builder.py — sanitize before any seed enters a prompt

INJECTION_PATTERNS = [
    r"ignore (previous|prior|all) instructions?",
    r"you are now",
    r"disregard (your|the|all) (previous|prior|system|above)",
    r"new (persona|role|instructions?|task)",
    r"act as",
    r"system: ",
    r"\[INST\]",
    r"<\|system\|>",
]

def sanitize_seed_document(text: str) -> str:
    import re
    for pattern in INJECTION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            logger.warning("Potential prompt injection in seed", extra={
                "pattern": pattern, "preview": text[:200]
            })
            # Replace the injection attempt with a placeholder
            text = re.sub(pattern, "[content filtered]", text, flags=re.IGNORECASE)
    return text
```

Apply `sanitize_seed_document()` to every RSS entry, Reddit post, and news article before it enters any prompt.

---

## GAP 8.2 — SSRF via Blog Webhook

**The Problem:**
The blog webhook endpoint accepts URLs and fetches content. If Ahmad's blog is ever compromised, an attacker could send Oybit to fetch internal Railway metadata endpoints (`169.254.169.254`, `localhost`, etc.).

**The Solution:**
```python
# backend/api/blog_webhook.py — URL allowlisting

from urllib.parse import urlparse
import ipaddress

ALLOWED_DOMAINS = [
    "ahmadportfolio.com",
    "yourportfolio.hashnode.dev",
    # add Ahmad's actual blog domain
]

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("169.254.0.0/16"),  # link-local (metadata services)
    ipaddress.ip_network("10.0.0.0/8"),       # private
    ipaddress.ip_network("172.16.0.0/12"),    # private
    ipaddress.ip_network("192.168.0.0/16"),   # private
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
]

def validate_webhook_url(url: str) -> bool:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain not in ALLOWED_DOMAINS:
        raise SecurityError(f"Domain not in allowlist: {domain}")

    # Also check resolved IP
    import socket
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(domain))
        for blocked_range in BLOCKED_IP_RANGES:
            if ip in blocked_range:
                raise SecurityError(f"Resolved IP {ip} is in blocked range")
    except socket.gaierror:
        raise SecurityError(f"Cannot resolve domain: {domain}")

    return True
```

---

## GAP 8.3 — Facebook App Credential Isolation

**The Problem:**
Facebook App ID + App Secret are master credentials — compromising them exposes ALL connected accounts, not just one token.

**The Solution:**
Store `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET` in Railway/Render environment variables labeled as "sensitive" (masked in UI). Never log them. Never include them in any debug output. Add a startup assertion:

```python
# backend/config.py
import os

def assert_secrets_not_in_logs():
    """Verify that secret values aren't accidentally hardcoded anywhere."""
    secrets_to_check = [
        os.environ.get("FACEBOOK_APP_SECRET"),
        os.environ.get("OPENROUTER_API_KEY"),
    ]
    # These should never appear in any source file
    # This is a reminder check — actual scanning should be in CI/CD
    assert all(s and len(s) > 10 for s in secrets_to_check), "Secrets not configured"
```

---

# PART 9 — LEARNING ENGINE IMPROVEMENTS

---

## GAP 9.1 — Engagement Rate Normalization

**The Problem:**
A post with 5 saves from 50 followers is proportionally much stronger than 5 saves from 5,000 followers. The learning engine currently treats both identically, causing early winning patterns to be underweighted as the account grows.

**The Solution:**

Add `followers_at_post_time` to `PostAnalytics` and normalize the engagement score:
```python
# backend/db/models.py — add to PostAnalytics
followers_at_post_time = Column(Integer)  # captured at publish time, never reconstructable later

# backend/analytics/scorer.py — normalized score
def compute_engagement_score(analytics: PostAnalytics) -> float:
    raw_score = (
        analytics.saves * 5 +
        analytics.shares * 3 +
        analytics.comments * 2 +
        analytics.follows * 5
    )
    # Normalize by follower count at post time
    if analytics.followers_at_post_time and analytics.followers_at_post_time > 0:
        normalized = raw_score / (analytics.followers_at_post_time / 1000)
    else:
        normalized = raw_score  # fallback if not captured

    return normalized
```

`followers_at_post_time` must be captured in the publisher at the moment of publish — NOT reconstructed later from analytics.

---

## GAP 9.2 — External Amplification Detection

**The Problem:**
A post reshared by a high-follower account will spike engagement artificially. The learning engine will incorrectly mark this as a top-performing pattern and try to replicate it. The performance was from the amplification, not the post quality.

**The Solution:**
```python
# backend/analytics/scorer.py — spike detection

ANOMALY_THRESHOLD_MULTIPLIER = 5  # 5x above account average = anomaly

def detect_external_amplification(post_analytics: PostAnalytics, account_avg_score: float) -> bool:
    if post_analytics.engagement_score > account_avg_score * ANOMALY_THRESHOLD_MULTIPLIER:
        logger.warning("Anomalous engagement spike detected — possible external amplification", extra={
            "post_id": post_analytics.post_id,
            "score": post_analytics.engagement_score,
            "account_avg": account_avg_score
        })
        return True
    return False
```

If amplification detected: flag the post in PatternDB with `externally_amplified=True`. The learning engine excludes these from pattern detection. Alert Ahmad via dashboard.

---

## GAP 9.3 — Content Cannibalisation Prevention

**The Problem:**
Posting twice on LinkedIn in one day — the second post suppresses the first. The scheduler doesn't know this.

**The Solution:**
```python
# backend/scheduler_worker/queue.py — spacing enforcement

MINIMUM_HOURS_BETWEEN_POSTS = {
    "linkedin": 8,         # LinkedIn: max 1 post per 8 hours
    "instagram_personal": 3,
    "instagram_brand": 6,
    "facebook": 4,
}

def can_post_to_account(account: str, proposed_time: datetime) -> tuple[bool, str]:
    last_post = session.query(Post).filter(
        Post.account == account,
        Post.status == "published"
    ).order_by(Post.published_at.desc()).first()

    if not last_post:
        return True, ""

    hours_since_last = (proposed_time - last_post.published_at).total_seconds() / 3600
    min_hours = MINIMUM_HOURS_BETWEEN_POSTS.get(account, 4)

    if hours_since_last < min_hours:
        return False, f"Too soon: {hours_since_last:.1f}h since last post (min {min_hours}h)"

    return True, ""
```

---

## GAP 9.4 — Sensitive Moment Detection (Tragedy Pause)

**The Problem:**
If a tragedy happens in Nigeria (flood, attack, prominent death), posting promotional/technical content that same day is tone-deaf. MiroFish correctly filters it out of new content, but pre-scheduled buffer posts still go out.

**The Solution:**
```python
# backend/intelligence/sentiment_guard.py — NEW

TRAGEDY_KEYWORDS = [
    "killed", "dead", "massacre", "bombing", "flood disaster",
    "protest crackdown", "attack", "obituary", "RIP", "mourning"
]

NIGERIA_CONTEXT_KEYWORDS = ["nigeria", "abuja", "lagos", "naira", "#nigeria"]

def check_for_sensitive_moment(trend_data: dict) -> tuple[bool, str]:
    """
    Called by mirofish_worker after trend aggregation.
    If a tragedy is detected in Nigerian context → pause all scheduled posts.
    """
    trending_texts = " ".join([item["title"] for item in trend_data.get("items", [])])

    tragedy_detected = any(kw in trending_texts.lower() for kw in TRAGEDY_KEYWORDS)
    nigeria_context = any(kw in trending_texts.lower() for kw in NIGERIA_CONTEXT_KEYWORDS)

    if tragedy_detected and nigeria_context:
        reason = "Potential tragedy detected in Nigerian context — all posts paused for manual review"
        logger.warning("SENSITIVE MOMENT DETECTED", extra={"reason": reason})

        # Pause all pending posts for next 24h
        session.query(SchedulerJob).filter(
            SchedulerJob.status == "pending",
            SchedulerJob.scheduled_at < datetime.now() + timedelta(hours=24)
        ).update({"status": "paused_sensitive", "last_error": reason})
        session.commit()

        # Notify Ahmad
        create_dashboard_alert(
            level="critical",
            message=reason,
            requires_action=True
        )
        return True, reason

    return False, ""
```

---

# PART 10 — NOTIFICATION DELIVERY

---

## GAP 10.1 — Alerts Must Actually Reach Ahmad (Telegram Self-Alert)

**The Problem:**
Currently alerts write to a `notifications` database table. Ahmad only sees them when he opens the dashboard — which could be days after a critical failure.

**The Solution:**

Oybit already has a Telegram publisher. Use the same Telegram bot to alert Ahmad when critical events happen:

```python
# backend/notifications/telegram_alert.py — NEW

import requests

def send_telegram_alert(message: str, level: str = "info") -> None:
    """
    Send alert to Ahmad's personal Telegram via the Oybit bot.
    level: info | warning | critical
    """
    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(level, "ℹ️")
    formatted = f"{emoji} *Oybit Alert*\n\n{message}"

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": AHMAD_TELEGRAM_CHAT_ID,  # env var: AHMAD_TELEGRAM_ID
            "text": formatted,
            "parse_mode": "Markdown"
        }
    )
```

**Critical events that trigger Telegram alert immediately:**
- Token expired and refresh failed for any account
- Meta app permission revoked
- MiroFish worker failed to run (all posts going silent)
- 3+ consecutive publish failures
- Engagement average dropped >30% for 7 days
- persona.md not updated in 30+ days (learning loop broken)
- Sensitive moment detected (posts paused)

**Non-critical events:** Dashboard notification only (not Telegram).

---

# PART 11 — PLATFORM ALGORITHM CORRECTIONS

---

## GAP 11.1 — Instagram Algorithm Reality (Strategy Corrections)

The current docs have several wrong assumptions about Instagram's algorithm. These must be corrected in `platforms/instagram_personal/strategy.md` and in the content generator's platform rules.

**Correction 1 — Reels > Carousels for reach:**
Reels currently get 5x the organic reach of carousels at the same engagement rate. The content cadence should be weighted: 5 Reels/week, 2 Carousels/week (not 4-5 carousels as currently planned).

**Correction 2 — First Reel is critical:**
Instagram boosts the first Reel from a new account to test content quality. If it underperforms, all subsequent Reels are suppressed for weeks. The first Reel must be the highest quality piece — manually selected by Ahmad, not auto-generated.

Add to Brand Voice Guardian for Instagram:
```python
INSTAGRAM_REEL_RULES = {
    "caption_visible_chars": 125,  # everything after 125 is hidden behind "more"
    "hook_must_land_in_chars": 125,
    "max_hashtags": 10,
    "hashtag_strategy": "interest_graph_not_hashtags",  # Reels use interest graph
    "min_duration_seconds": 3,
    "max_duration_seconds": 90,
    "aspect_ratio": "9:16"
}
```

**Correction 3 — Stories don't contribute to feed algorithm:**
Stories are conversion tools (lurker → follower), not reach tools. Strategy should be: Stories are for profile visitors who are deciding whether to follow. Each Story should give a reason to follow NOW. Remove Stories from the automated pipeline — they should be casual, manual, and authentic. Oybit should not automate Stories.

---

## GAP 11.2 — LinkedIn Algorithm Reality (Strategy Corrections)

**Correction 1 — Dwell time is the primary signal:**
LinkedIn measures how long people read your post. A 1,500-word post that takes 3 minutes to read outperforms a 200-word post with more likes. Update `platform_rules.py`:
```python
LINKEDIN_RULES = {
    "min_chars_for_dwell": 600,       # below this, not enough reading time
    "max_chars_sweet_spot": 1300,
    "line_break_every_n_chars": 100,  # force line breaks for readability
    "never_start_with": ["I ", "I'm"],
    "max_hashtags": 5,
    "emoji_max": 3,
    "golden_hour_post_check": True,   # post during 8-10AM WAT
}
```

**Correction 2 — Polls for reach:**
LinkedIn polls get 3–5x more reach than text posts currently. Add `poll` as a PostType for LinkedIn:
```python
# backend/publishers/linkedin.py — add poll method

def post_linkedin_poll(question: str, options: list, duration_days: int = 7) -> str:
    """
    LinkedIn polls via ugcPosts with pollContent
    max 4 options, max 30 chars per option
    """
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": question},
                "shareMediaCategory": "NONE",
                "pollContent": {
                    "question": question,
                    "options": [{"text": opt} for opt in options[:4]],
                    "settings": {
                        "duration": {"unit": "DAY", "duration": duration_days}
                    }
                }
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
```

---

## GAP 11.3 — Facebook Reality (Strategy Correction)

The current docs plan to use Facebook page posts as a growth strategy. This is wrong for 2026.

**The reality:**
- Facebook page organic reach: 2–5% of followers
- Facebook Groups: where organic reach actually exists
- Facebook Reels (not regular videos): get boosted reach

**Updated strategy in `platforms/facebook/strategy.md`:**
1. Facebook page posts = **repurposing only** (already correct)
2. Ahmad posting personally in Groups = **primary Facebook growth tactic** (handled by GAP 2.1)
3. Videos uploaded to page should be **Reels format** (9:16, native upload) — not links to Instagram
4. Facebook is lowest priority (already correct)

---

# PART 12 — REAL EVENT INGESTION

---

## GAP 12.1 — "What Just Happened" Input (The Authenticity Problem)

**The Problem:**
The system generates synthetic authenticity by rephrasng existing themes. It cannot generate NEW real moments. Over time, content starts recycling. Real events (Ahmad's 2AM shipping moments, first customer, found a bug) are always more authentic and higher-performing than predicted narratives. There is no mechanism for Ahmad to log these.

**The Solution:**

Add a Telegram bot listener as the primary real-event input:
```python
# backend/event_ingestion/telegram_listener.py — NEW

from telegram import Update
from telegram.ext import Application, MessageHandler, filters

async def handle_message(update: Update, context) -> None:
    """
    Ahmad messages the Oybit Telegram bot describing what just happened.
    "just shipped the pre-publish gate, 3am, took way longer than expected"
    → Oybit creates a high-priority content brief
    """
    if str(update.effective_chat.id) != AHMAD_TELEGRAM_CHAT_ID:
        return  # Only Ahmad can trigger this

    event_text = update.message.text
    logger.info("Real event received from Ahmad", extra={"event": event_text})

    # Create a high-priority topic brief that bypasses MiroFish
    brief = {
        "source": "real_event",
        "priority": "high",
        "raw_event": event_text,
        "timestamp": datetime.now().isoformat(),
        "bypass_mirofish": True  # Real events go straight to generation
    }

    # AI expands the raw event into a structured brief
    expanded_brief = expand_real_event_brief(event_text)

    # Inject into the content queue at top priority
    create_top_priority_brief(expanded_brief)

    await update.message.reply_text(
        "Got it. Generating content brief from your real moment — will be in approval queue in ~60 seconds."
    )
```

Also add a dashboard "Log Real Event" button that does the same thing via web UI.

---

# PART 13 — API LAYER & RATE LIMITS

---

## GAP 13.1 — Rate Limit Budget Manager

**The Problem:**
Meta's API rate limits are per-app (not per-account). Both Instagram accounts share the same limit. Heavy analytics polling eats into publish capacity. During high-volume periods, publishing can be blocked.

**The Solution:**
```python
# backend/api/rate_limit_manager.py — NEW

PLATFORM_BUDGETS = {
    "meta": {
        "calls_per_hour": 200,
        "publish_reserve": 50,   # keep 50 calls reserved for publishing
        "analytics_ceiling": 150  # analytics can use up to 150/hour
    },
    "linkedin": {
        "calls_per_hour": 100,
        "publish_reserve": 20,
        "analytics_ceiling": 80
    }
}

class RateLimitManager:
    def __init__(self):
        self._counters = {}  # platform → (count, window_start)

    def can_make_call(self, platform: str, call_type: str) -> bool:
        budget = PLATFORM_BUDGETS.get(platform)
        current_count = self._get_current_count(platform)

        if call_type == "publish":
            # Publishing always allowed if we haven't hit total ceiling
            return current_count < budget["calls_per_hour"]
        elif call_type == "analytics":
            # Analytics backed off when we're near the reserve threshold
            remaining = budget["calls_per_hour"] - current_count
            return remaining > budget["publish_reserve"]

        return True
```

---

## GAP 13.2 — Reddit Anti-Detection

**The Problem:**
Reddit shadowbans accounts that post with bot-like patterns (exact timing, no delays, rapid sequences).

**The Solution:**
```python
# backend/publishers/reddit_commenter.py — human-timing simulation

import random

def randomized_delay(base_seconds: int = 60, variance_pct: float = 0.5) -> None:
    """Add human-like randomness to timing."""
    variance = base_seconds * variance_pct
    delay = base_seconds + random.uniform(-variance, variance)
    time.sleep(max(delay, 10))  # minimum 10 seconds

# All Reddit posting calls:
# 1. Randomize within ±30 min of scheduled time
# 2. Never post more than 2x per day per subreddit
# 3. Always wait 30-120s between any Reddit actions
# 4. Comment quality > promotional content ratio: 10:1 minimum
```

---

# PART 14 — DEPENDENCY PINNING

---

## GAP 14.1 — Exact Version Pinning (requirements.txt)

**The Problem:**
OASIS, GraphRAG, Playwright, and atproto all have breaking changes between minor versions. Unpinned installs will break on Railway redeploy when a new version ships.

**The Solution:**

`requirements.txt` must use exact versions:
```
# AI / Intelligence
openrouter-py==0.x.x          # pin exact
graphrag==0.x.x               # pin exact — has known breaking changes between minors
oasis-social==0.x.x           # pin exact — research software, unpredictable updates
zep-cloud==0.x.x              # pin exact

# Platform APIs
requests==2.31.0
praw==7.7.1
atproto==0.x.x                # pin exact — Bluesky protocol still evolving

# Rendering
playwright==1.44.0            # pin exact — browser binary version tied to this
Jinja2==3.1.4
Remotion pinned in package.json

# Database
SQLAlchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.4

# FastAPI
fastapi==0.111.0
uvicorn==0.30.1
```

Pin Playwright's browser version:
```bash
# In Dockerfile / install script — don't just `playwright install chromium`
playwright install chromium@1.44.0  # pin to same version as the Python package
```

---

# PART 15 — USER EXPERIENCE & HUMAN FEEDBACK

---

## GAP 15.1 — Real-Time Feedback UI

**The Problem:**
The only human feedback mechanisms are the approval queue and the post-authenticity rating. Ahmad can't signal "more of this exact style" or "stop this pattern" from a published post in real-time.

**The Solution:**

Add to every published post card in the dashboard:
- 👍 "More like this" — immediately boosts that pattern's weight in PatternDB
- 👎 "Stop this pattern" — flags that pattern as suppressed
- "Why did Oybit post this?" — shows the decision chain (which narrative, gate score, what persona section was used)

```python
# backend/api/feedback.py — NEW endpoints

@router.post("/posts/{post_id}/feedback")
async def post_feedback(post_id: str, feedback: PostFeedbackRequest):
    post = get_post(post_id)

    if feedback.signal == "more_like_this":
        # Boost pattern weight in PatternDB by 20%
        boost_pattern(post.hook_type, post.topic_pillar, post.format, post.account, boost=1.2)
        audit_log.write(event_type="manual_feedback", decision="boost", entity_id=post_id)

    elif feedback.signal == "stop_this":
        # Suppress pattern in PatternDB
        suppress_pattern(post.hook_type, post.topic_pillar, post.format, post.account)
        audit_log.write(event_type="manual_feedback", decision="suppress", entity_id=post_id)

@router.post("/emergency_pause")
async def emergency_pause(hours: int = 24):
    """One button that stops all scheduled posts for N hours."""
    session.query(SchedulerJob).filter(
        SchedulerJob.status == "pending"
    ).update({"status": "paused_manual"})
    session.commit()
    logger.warning("Emergency pause activated", extra={"hours": hours})
```

---

## GAP 15.2 — Mobile-First Approval UX

**The Problem:**
Ahmad is not always at a computer. The approval flow must work in 3 taps on mobile.

**The Solution:**

The approval queue page in Next.js must be built mobile-first:
- Full-width post preview card
- Score badge visible without scrolling
- Approve (green) / Reject (red) buttons as full-width bottom-fixed buttons
- Swipe right = approve, swipe left = reject
- Pinch to preview carousel slides
- No actions require keyboard input

---

## GAP 15.3 — "Why Did Oybit Post This?" Transparency Layer

**The Problem:**
If Ahmad can't understand what the system is doing, he'll micromanage it and the autonomy breaks.

**The Solution:**

Every post must carry its full reasoning chain in the database. The dashboard shows this on demand:

```
📊 Post Intelligence Report
━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Narrative Source
MiroFish found a rising conversation around "indie hackers shipping without VC validation"
Confidence: 78% | Detected at: 5:23 AM WAT

✅ Opportunity Check
Passed Content DNA: System insight ✓ | Real consequence ✓
Persona alignment: 0.87 | Topic pillar: Building in Public (30% weight)

⚡ Hook Selected
Type: "Consequence hook"
PatternDB avg score for this hook on LinkedIn: 4.2 (above your 3.1 average)

🎯 Gate Result
PASS | Confidence: 0.71
Agent reactions: 68% engaged, 12% shared, 20% ignored
Best posting time: 09:00 WAT (recommended by gate)

📈 Prediction vs Reality (48h)
Predicted score: 18 | Actual score: 23 (+28%)
```

---

# PART 16 — MiroFish-SPECIFIC FIXES

---

## GAP 16.1 — Zep Free Tier Rate Limit (Default Agent Count)

**The Problem:**
Zep Cloud free tier has ~1,000 memory operations per month. 500 agents × 4 rounds × daily = the free tier blows in 2 days.

**The Solution:**
Change defaults:
```bash
# .env
MIROFISH_AGENT_COUNT=20          # default for free tier
# MIROFISH_AGENT_COUNT=500       # uncomment when on paid Zep + paid Railway
```

Add runtime warning:
```python
# workers/mirofish_worker.py
if MIROFISH_AGENT_COUNT > 100 and ZEP_TIER == "free":
    logger.warning("High agent count with free Zep tier — will exhaust quota quickly")
```

---

## GAP 16.2 — GraphRAG Initialization Check

**The Problem:**
GraphRAG requires `graphrag init` to create required config files. If this step was skipped, `graph_builder.py` fails on first run with a config error that looks unrelated.

**The Solution:**
```python
# backend/intelligence/mirofish/graph_builder.py — startup check

import subprocess, os

def verify_graphrag_initialized(project_dir: str) -> None:
    required_files = [
        os.path.join(project_dir, "settings.yaml"),
        os.path.join(project_dir, ".env"),
    ]
    missing = [f for f in required_files if not os.path.exists(f)]

    if missing:
        logger.info("GraphRAG not initialized — running graphrag init")
        result = subprocess.run(
            ["graphrag", "init", "--root", project_dir],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"GraphRAG init failed: {result.stderr}")
```

Call `verify_graphrag_initialized()` at the top of `mirofish_worker.py` before anything else runs.

---

## GAP 16.3 — Content Buffer (Cascade Failure Prevention)

**The Problem:**
If MiroFish fails at 5AM, the entire pipeline stops. All 4 accounts go silent. One bad morning costs a week of algorithmic momentum.

**The Solution:**
```python
# backend/feedback_loop/buffer_manager.py — NEW

BUFFER_SIZE_DAYS = 3  # Always maintain 3 days of pre-approved posts per account

def check_and_fill_buffer() -> None:
    """
    Called by feedback_worker weekly and by mirofish_worker after each run.
    Ensures buffer always has 3 days of fallback content.
    """
    for account in ["linkedin", "instagram_personal", "instagram_brand", "facebook"]:
        buffered_count = count_buffer_posts(account)
        posts_per_day = get_account_daily_cadence(account)
        needed = (BUFFER_SIZE_DAYS * posts_per_day) - buffered_count

        if needed > 0:
            logger.info(f"Refilling buffer for {account}", extra={"needed": needed})
            generate_buffer_posts(account, count=needed)

def use_buffer_if_mirofish_failed(account: str) -> list:
    """Called by dispatcher when no regular posts are queued."""
    buffer_posts = get_buffer_posts(account, limit=1)
    if buffer_posts:
        logger.warning("Using buffer post — MiroFish may have failed", extra={"account": account})
    return buffer_posts
```

---

# PART 17 — TIMEZONE & CALENDAR

---

## GAP 17.1 — All Times in UTC, Display in WAT

**The Problem:**
If Agent A stores `scheduled_at` in WAT and Agent B stores it in UTC, posts fire an hour wrong or at unpredictable times after a timezone edge case.

**The Solution:**
```python
# backend/config.py — canonical timezone rule

import pytz

STORAGE_TIMEZONE = pytz.UTC           # ALL times in DB are UTC
DISPLAY_TIMEZONE = pytz.timezone("Africa/Lagos")  # WAT = UTC+1

def to_storage_time(display_time: datetime) -> datetime:
    """Convert WAT display time to UTC for storage."""
    if display_time.tzinfo is None:
        display_time = DISPLAY_TIMEZONE.localize(display_time)
    return display_time.astimezone(pytz.UTC)

def to_display_time(storage_time: datetime) -> datetime:
    """Convert UTC storage time to WAT for display."""
    return storage_time.replace(tzinfo=pytz.UTC).astimezone(DISPLAY_TIMEZONE)
```

**Rule:** Every `datetime` object written to the DB goes through `to_storage_time()`. Every `datetime` shown to Ahmad goes through `to_display_time()`. No exceptions.

---

## GAP 17.2 — Campaign Mode (Coordinated Cross-Account Posting)

**The Problem:**
When ColdSift or Volari Finance has a launch moment, all 4 accounts should post a coordinated narrative arc — not independent posts about unrelated topics.

**The Solution:**
```python
# backend/db/models.py — add Campaign model

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    trigger_event = Column(String)      # "coldsift_launch", "volari_beta", etc.
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    narrative_arc = Column(JSON)        # {"day1": "teaser", "day2": "reveal", "day3": "social proof"}
    accounts = Column(JSON)             # which accounts participate and in what order
    status = Column(String)             # planning | active | completed
```

During a campaign, the scheduler overrides normal MiroFish briefs for participating accounts and uses campaign narrative arc posts instead.

---

# PART 18 — ABSOLUTE VERIFICATION CHECKLIST

Run this in order after merging both agents' code. Do NOT deploy until all pass.

```bash
# 1. Import chain check — the most critical
python -c "from backend.db.models import *; print('✅ Models OK')"
python -c "from backend.main import app; print('✅ App import OK')"

# 2. Single Base check
python -c "
from backend.db.models import *
import sqlalchemy.orm
bases = [v for v in globals().values() if isinstance(v, type) and hasattr(v, '__tablename__')]
base_classes = set(type(b).__bases__[0] for b in bases if hasattr(type(b), '__bases__'))
print(f'✅ Base count: {len(base_classes)} (must be 1)')
"

# 3. Migration check
alembic heads  # must show exactly 1 head
alembic upgrade head  # must run clean

# 4. Config check — both agents must use same env var names
python -c "from backend.config import settings; print('✅ Config OK')"

# 5. Playwright check
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); print('✅ Playwright OK')"

# 6. Volume mount check (on Railway)
python -c "
import os
assert os.path.exists('/data/personas/ahmad'), '❌ Persona volume not mounted'
assert os.path.exists('/data'), '❌ Queue volume not mounted'
print('✅ Volumes OK')
"

# 7. All 4 platform connections
python scripts/verify_connections.py

# 8. GraphRAG init
python -c "from backend.intelligence.mirofish.graph_builder import verify_graphrag_initialized; verify_graphrag_initialized('./graphrag_project'); print('✅ GraphRAG OK')"

# 9. Worker dry run
python workers/mirofish_worker.py --dry-run
python workers/analytics_worker.py --dry-run

# 10. Health endpoint depth
curl http://localhost:8000/health | python -m json.tool
# Verify: database=ok, redis=ok, volume=ok, queue_db=ok
```

---

*This document covers every identified gap. Every agent building any part of Oybit must read this entire document before writing a single line of code. Where this document conflicts with the 8 core docs, this document wins.*
