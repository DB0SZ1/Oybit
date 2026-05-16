# GAPS_FINAL.md — Remaining Gap Completions
# Read this AFTER OYBIT_GAP_SOLUTIONS.md and GAPS_AND_FIXES.md.
# This file fills everything those two missed.
# All three gap files together = complete gap coverage.

---

# PART 1 — MISSING PUBLISHERS AND POST TYPES

---

## GAP 1.1 — LinkedIn Polls Publisher

**The Problem:**
LinkedIn polls currently outperform all other content formats for organic reach. Zero implementation anywhere.

**The Solution:**

```python
# backend/publishers/linkedin_poll.py — NEW

def create_linkedin_poll(question: str, options: list[str],
                          duration_days: int = 7) -> str:
    """
    LinkedIn polls via ugcPosts with POLL shareMediaCategory.
    Max 4 options. Duration: 1, 3, 7, or 14 days only.
    Character limits: question 140 chars, each option 30 chars.
    """
    if len(options) > 4 or len(options) < 2:
        raise ValueError("LinkedIn polls require 2-4 options")
    if len(question) > 140:
        raise ValueError(f"Poll question too long: {len(question)} chars (max 140)")
    for opt in options:
        if len(opt) > 30:
            raise ValueError(f"Poll option too long: '{opt}' ({len(opt)} chars, max 30)")
    if duration_days not in [1, 3, 7, 14]:
        raise ValueError(f"Duration must be 1, 3, 7, or 14 days")

    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": ""},  # caption above poll (optional)
                "shareMediaCategory": "URN_REFERENCE",
                "media": [{
                    "status": "READY",
                    "media": "urn:li:digitalmediaAsset:poll",
                }]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        # Poll-specific structure
        "poll": {
            "question": question,
            "options": [{"text": opt} for opt in options],
            "settings": {
                "duration": f"SEVEN_DAYS" if duration_days == 7 else
                            f"ONE_DAY" if duration_days == 1 else
                            f"THREE_DAYS" if duration_days == 3 else "FOURTEEN_DAYS",
                "isVoterVisible": False,
                "isResultPublic": True
            }
        }
    }

    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        json=payload,
        headers={
            "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    )

    if response.status_code not in [200, 201]:
        handle_linkedin_error(response, payload)

    return response.headers.get("x-restli-id", "")
```

**Poll generation in content generator:**

Content generator must know when to generate a poll vs a text post. Add to `backend/content/platform_rules.py`:

```python
LINKEDIN_POLL_TRIGGERS = [
    "opinion",
    "what do you think",
    "which would you",
    "agree or disagree",
    "your experience",
    "have you ever",
    "do you prefer"
]

def should_generate_poll(brief: str, platform: str) -> bool:
    if platform != "linkedin":
        return False
    brief_lower = brief.lower()
    return any(trigger in brief_lower for trigger in LINKEDIN_POLL_TRIGGERS)
```

Add `PostType.LINKEDIN_POLL` to the PostType enum in both publishers.

---

## GAP 1.2 — Instagram Stories Separate Module

**The Problem:**
Stories are currently treated as just another post format. They have a completely different purpose (converting profile visitors to followers, not reach), different content strategy, and different API flow.

**The Solution:**

```python
# backend/publishers/instagram_stories.py — NEW

class InstagramStoriesPublisher:
    """
    Stories strategy: convert profile visitors → followers.
    NOT for reach. NOT for discovery.
    
    Best Story content types:
    - Behind the scenes (photo/short video)
    - Polls ("which do you prefer?")
    - Questions ("ask me anything about building X")
    - Link in bio CTAs after a Reel goes out
    - Countdown timers for product launches
    """

    def post_photo_story(self, image_path: str, account: str) -> str:
        """Upload a photo story."""
        image_url = upload_to_cdn(image_path)
        container = self._create_story_container(image_url, "IMAGE", account)
        self._wait_for_ready(container, account)
        return self._publish_container(container, account)

    def post_video_story(self, video_path: str, account: str) -> str:
        """Upload a video story (max 60 seconds)."""
        video_url = upload_to_cdn(video_path)
        container = self._create_story_container(video_url, "VIDEO", account)
        self._wait_for_ready(container, account)
        return self._publish_container(container, account)

    def _create_story_container(self, media_url: str,
                                 media_type: str, account: str) -> str:
        token = get_token(account)
        user_id = get_user_id(account)
        payload = {
            "media_type": "STORIES",
            "access_token": token
        }
        if media_type == "IMAGE":
            payload["image_url"] = media_url
        else:
            payload["video_url"] = media_url

        response = requests.post(
            f"{META_BASE_URL}/{user_id}/media",
            data=payload
        )
        data = check_meta_response(response.json(), account)
        return data["id"]

    def _wait_for_ready(self, container_id: str, account: str,
                         max_wait: int = 60) -> None:
        token = get_token(account)
        for _ in range(max_wait):
            response = requests.get(
                f"{META_BASE_URL}/{container_id}",
                params={"fields": "status_code", "access_token": token}
            )
            status = response.json().get("status_code")
            if status == "FINISHED":
                return
            elif status == "ERROR":
                raise StoryUploadError(f"Container {container_id} errored")
            time.sleep(1)
        raise StoryUploadError(f"Container {container_id} timed out after {max_wait}s")

    def _publish_container(self, container_id: str, account: str) -> str:
        token = get_token(account)
        user_id = get_user_id(account)
        response = requests.post(
            f"{META_BASE_URL}/{user_id}/media_publish",
            data={"creation_id": container_id, "access_token": token}
        )
        data = check_meta_response(response.json(), account)
        return data["id"]
```

**Stories content strategy — separate from feed content:**

```python
# backend/intelligence/stories_strategy.py — NEW

STORIES_CONTENT_TYPES = [
    "behind_the_scenes",    # photo/video of Ahmad building
    "poll",                 # "Which would you use?" engagement
    "question_box",         # "Ask me anything about X"
    "link_cta",             # "New post out — link in bio"
    "countdown",            # product launch countdown
    "repost_from_feed",     # reshare a feed post to Stories
]

def generate_story_brief(context: str, story_type: str) -> dict:
    """
    Stories briefs are simpler than feed briefs.
    Short, visual, action-oriented.
    """
    return {
        "type": story_type,
        "context": context,
        "duration": "24h",
        "platform": "instagram",
        "format": "story",
        "objective": "convert_profile_visitor_to_follower"
    }

def schedule_story_after_reel(reel_post_id: int) -> None:
    """
    Automatically schedule a link CTA story 30 minutes after a Reel posts.
    "Just dropped a new Reel — check it out 👆"
    """
    story_time = get_post_scheduled_at(reel_post_id) + timedelta(minutes=30)
    create_story_job(
        story_type="link_cta",
        context=f"Reel just posted — drive profile visits to follow",
        scheduled_at=story_time,
        account="instagram_personal"
    )
```

---

## GAP 1.3 — Facebook Reels Publisher

**The Problem:**
Facebook Reels get significantly boosted organic reach compared to regular video uploads. Current `facebook.py` only handles regular video. These are different API calls.

**The Solution:**

```python
# backend/publishers/facebook.py — add Reels method

def post_facebook_reel(video_path: str, description: str,
                        page_id: str, page_token: str) -> str:
    """
    Facebook Reels: different from regular video upload.
    Requires: video_reels upload endpoint, NOT /videos
    Format: 9:16 aspect ratio, 3-90 seconds, max 1GB

    Search: "Facebook Graph API reels upload" for latest endpoint
    Current known flow (verify against latest docs):
    """

    # Step 1: Initialize Reels upload session
    init_response = requests.post(
        f"{META_BASE_URL}/{page_id}/video_reels",
        data={
            "upload_phase": "start",
            "access_token": page_token
        }
    )
    init_data = check_meta_response(init_response.json(), "facebook_reel")
    video_id = init_data["video_id"]
    upload_url = init_data["upload_url"]

    # Step 2: Upload video binary
    file_size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        upload_response = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {page_token}",
                "offset": "0",
                "file_size": str(file_size)
            },
            data=f.read()
        )

    # Step 3: Finish upload
    finish_response = requests.post(
        f"{META_BASE_URL}/{page_id}/video_reels",
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description,
            "access_token": page_token
        }
    )
    data = check_meta_response(finish_response.json(), "facebook_reel")
    return video_id
```

---

# PART 2 — GROWTH MECHANICS

---

## GAP 2.1 — Follow Strategy Module

**The Problem:**
Strategic following on Instagram triggers follow-backs and profile visits. No implementation anywhere. Ahmad needs to make an informed decision about using this.

**Important note:** This is borderline Instagram ToS. It is widely used but technically against "inauthentic behavior" policy. Ahmad must consciously choose whether to enable this. It is OFF by default.

**The Solution:**

```python
# backend/growth/follow_strategy.py — NEW
# DISABLED BY DEFAULT — enable via FOLLOW_STRATEGY_ENABLED=true env var

import os

FOLLOW_STRATEGY_ENABLED = os.getenv("FOLLOW_STRATEGY_ENABLED", "false").lower() == "true"
MAX_FOLLOWS_PER_DAY = int(os.getenv("MAX_FOLLOWS_PER_DAY", "50"))  # safe limit (Instagram flags at 200+)
UNFOLLOW_AFTER_DAYS = int(os.getenv("UNFOLLOW_AFTER_DAYS", "7"))

class FollowStrategyManager:

    def find_accounts_to_follow(self, account: str) -> list[str]:
        """
        Find accounts in Ahmad's niche who haven't followed back yet.
        Strategy: follow followers of top accounts in niche.
        """
        if not FOLLOW_STRATEGY_ENABLED:
            return []

        target_accounts = get_niche_seed_accounts(account)  # stored in DB
        candidates = []

        for seed_account in target_accounts[:3]:  # limit to 3 seed accounts per run
            followers = self.fetch_seed_followers(seed_account, limit=100)
            for follower in followers:
                if not self.already_following(follower, account):
                    if not self.already_followed_and_unfollowed(follower, account):
                        candidates.append(follower)

        return candidates[:MAX_FOLLOWS_PER_DAY]

    def execute_follow_batch(self, candidates: list[str], account: str) -> int:
        """Follow candidates with human-like timing."""
        import random
        followed = 0

        for candidate in candidates:
            if followed >= MAX_FOLLOWS_PER_DAY:
                break

            self.follow_account(candidate, account)
            self.record_follow(candidate, account)
            followed += 1

            # Human-like delay: 30-90 seconds between follows
            time.sleep(random.uniform(30, 90))

        return followed

    def unfollow_non_reciprocators(self, account: str) -> int:
        """Unfollow accounts that didn't follow back after UNFOLLOW_AFTER_DAYS."""
        cutoff = datetime.utcnow() - timedelta(days=UNFOLLOW_AFTER_DAYS)

        stale_follows = db.query(FollowRecord).filter(
            FollowRecord.account == account,
            FollowRecord.followed_at < cutoff,
            FollowRecord.followed_back == False,
            FollowRecord.unfollowed_at.is_(None)
        ).all()

        unfollowed = 0
        for record in stale_follows:
            self.unfollow_account(record.target_account_id, account)
            record.unfollowed_at = datetime.utcnow()
            unfollowed += 1
            time.sleep(random.uniform(10, 30))

        db.commit()
        return unfollowed
```

**Add `FollowRecord` to models:**
```python
class FollowRecord(Base):
    __tablename__ = "follow_records"
    id = Column(Integer, primary_key=True)
    account = Column(String)                    # which of Ahmad's accounts
    target_account_id = Column(String)          # who was followed
    target_account_handle = Column(String)
    followed_at = Column(DateTime)
    followed_back = Column(Boolean, default=False)
    followed_back_at = Column(DateTime, nullable=True)
    unfollowed_at = Column(DateTime, nullable=True)
    source_seed_account = Column(String)        # which seed account led to this
```

---

## GAP 2.2 — Saved Reply Templates

**The Problem:**
When a post goes viral, 200 people ask "how did you build this?" Generating a unique OpenRouter reply for each is slow and expensive. Need template-based personalization.

**The Solution:**

```python
# backend/reply_manager/saved_templates.py — NEW

class SavedReplyTemplate(Base):
    __tablename__ = "saved_reply_templates"
    id = Column(Integer, primary_key=True)
    trigger_category = Column(String)   # question_how_built|praise|criticism|networking|help_request
    template_text = Column(Text)        # template with {{placeholders}}
    platform = Column(String)           # linkedin|instagram_personal|instagram_brand|facebook|all
    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

# Pre-populate with Ahmad's common response patterns:
DEFAULT_TEMPLATES = [
    {
        "trigger_category": "question_how_built",
        "template_text": "Built with {{stack}}. The hardest part was {{challenge}}. Full writeup on my blog — link in bio.",
        "platform": "all"
    },
    {
        "trigger_category": "praise",
        "template_text": "Appreciate it! {{specific_acknowledgment}} — more coming.",
        "platform": "linkedin"
    },
    {
        "trigger_category": "networking",
        "template_text": "Thanks for reaching out. {{context_note}} — feel free to DM if you want to connect properly.",
        "platform": "linkedin"
    },
    {
        "trigger_category": "help_request",
        "template_text": "Happy to help — {{answer_brief}}. Drop a follow for more content like this.",
        "platform": "instagram_personal"
    }
]
```

**Template-based reply drafter:**

```python
# backend/reply_manager/drafter.py — modify existing

def draft_reply(comment: Reply, persona_path: Path) -> str:
    """
    Check for matching template first (fast + cheap).
    Fall back to OpenRouter only if no template matches.
    """
    category = classify_comment_category(comment.comment_text)
    template = get_matching_template(category, comment.platform)

    if template:
        # Use template + minimal OpenRouter call to fill placeholders
        filled = fill_template_placeholders(
            template.template_text,
            comment.comment_text,
            persona_path
        )
        update_template_use_count(template.id)
        return filled
    else:
        # Full OpenRouter generation for novel comment types
        return generate_reply_from_scratch(comment, persona_path)

def fill_template_placeholders(template: str, comment: str,
                                persona_path: Path) -> str:
    """
    Only fills {{placeholders}} — much cheaper than full generation.
    Single short OpenRouter call vs full generation.
    """
    placeholders = re.findall(r'\{\{(\w+)\}\}', template)
    if not placeholders:
        return template

    prompt = f"""
    Fill in these placeholders for a reply template.
    Comment received: {comment}
    Template: {template}
    Placeholders to fill: {placeholders}
    
    Return ONLY a JSON object with placeholder names as keys.
    Keep values SHORT (under 15 words each).
    Sound like Ahmad — direct, technical, genuine.
    """

    response = call_openrouter({"messages": [{"role": "user", "content": prompt}],
                                 "max_tokens": 200})
    fills = json.loads(response["choices"][0]["message"]["content"])

    result = template
    for placeholder, value in fills.items():
        result = result.replace(f"{{{{{placeholder}}}}}", value)

    return result
```

---

## GAP 2.3 — Gross Follows Tracking

**The Problem:**
The analytics collector captures follows at the 48h mark. But if 20 accounts followed and 15 unfollowed within that window, the net is 5 — masking what was actually a good post. Need gross follows, not net.

**The Solution:**

```python
# backend/analytics/aggregator.py — modify follows collection

def collect_post_analytics(post_id: int, platform_post_id: str,
                            account: str) -> PostAnalytics:
    """
    For follows: capture GROSS follows gained from this post,
    not net account change.
    Instagram provides 'follows' in insights — this is gross follows
    attributed to the post, not account-level net change.
    """

    # Instagram: /insights?metric=follows gives post-attributed follows
    # This is gross (people who followed from this post) not net
    insights = fetch_instagram_post_insights(
        platform_post_id, account,
        metrics=["reach", "impressions", "likes", "comments",
                 "shares", "saved", "follows"]  # 'follows' = gross post-attributed
    )

    # Also capture account-level follower snapshot for normalization
    current_followers = fetch_current_follower_count(account)

    analytics = PostAnalytics(
        post_id=post_id,
        account=account,
        reach=insights.get("reach", 0),
        impressions=insights.get("impressions", 0),
        likes=insights.get("likes", 0),
        comments=insights.get("comments", 0),
        shares=insights.get("shares", 0),
        saves=insights.get("saved", 0),
        follows_gross=insights.get("follows", 0),  # NEW FIELD: gross post-attributed
        followers_at_measurement=current_followers,  # snapshot for rate calculation
        measured_at=datetime.utcnow()
    )

    # Engagement score uses gross follows
    analytics.engagement_score = compute_engagement_score(analytics)
    return analytics
```

**Add `follows_gross` and `followers_at_measurement` to PostAnalytics model.**

---

# PART 3 — AUDIENCE INTELLIGENCE

---

## GAP 3.1 — Comment Sentiment Analysis

**The Problem:**
One comment "This is exactly what I needed, bookmarking this" is worth 100 "nice post!" comments. Current system counts comments but doesn't assess quality.

**The Solution:**

```python
# backend/analytics/comment_analyzer.py — NEW

COMMENT_CATEGORIES = {
    "high_value": ["exactly what I needed", "bookmarked", "saved this",
                   "sharing with my team", "implemented this", "used this",
                   "this solved", "been looking for this"],
    "question": ["how did you", "what did you use", "can you explain",
                 "where can I", "how do I", "?"],
    "praise": ["great", "amazing", "love this", "excellent", "nice",
               "good post", "well done"],
    "criticism": ["wrong", "disagree", "not true", "actually",
                  "you're missing", "this is bad"],
    "spam": ["follow back", "check my", "dm me", "buy", "click here"]
}

def analyze_comment_quality(comment_text: str) -> dict:
    """
    Classify and score comment quality.
    High-value comments are the real signal.
    """
    text_lower = comment_text.lower()
    category = "generic"
    quality_score = 1.0  # base score

    for cat, keywords in COMMENT_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            category = cat
            break

    quality_multipliers = {
        "high_value": 5.0,   # "this solved my problem" = 5x a like
        "question": 2.0,     # engaged enough to ask = 2x
        "praise": 1.0,       # generic praise = baseline
        "criticism": 1.5,    # criticism means they cared
        "spam": 0.0,         # spam = zero signal
        "generic": 0.5       # "nice" = half signal
    }

    quality_score = quality_multipliers.get(category, 1.0)
    word_count = len(comment_text.split())
    if word_count > 20:
        quality_score *= 1.5  # longer comments = more invested

    return {
        "category": category,
        "quality_score": quality_score,
        "word_count": word_count
    }

def compute_weighted_comment_score(comments: list[dict]) -> float:
    """Replace raw comment count with quality-weighted score."""
    total = 0.0
    for comment in comments:
        analysis = analyze_comment_quality(comment["text"])
        total += analysis["quality_score"]
    return total
```

**Add `comment_quality_score` to PostAnalytics model and update engagement formula:**
```python
# Updated engagement score incorporating comment quality
def compute_engagement_score(analytics: PostAnalytics) -> float:
    return (
        analytics.saves * 5 +
        analytics.shares * 3 +
        analytics.comment_quality_score * 3 +  # quality-weighted, not raw count
        analytics.follows_gross * 5
    )
```

---

## GAP 3.2 — Profile Visits Tracking

**The Problem:**
Profile visits from a post = warm leads. Someone read the post, was interested, visited the profile. This is a critical metric that's not being tracked.

**The Solution:**

```python
# backend/analytics/aggregator.py — add profile visits

# Instagram provides profile_activity in post insights
# Includes: profile_visits, website_clicks, call_clicks

def collect_instagram_profile_metrics(post_id: str, account: str) -> dict:
    insights = fetch_instagram_post_insights(
        post_id, account,
        metrics=["profile_activity"]
    )
    # profile_activity returns: profile_visits, website_clicks
    return {
        "profile_visits": insights.get("profile_visits", 0),
        "website_clicks": insights.get("website_clicks", 0),
    }

# LinkedIn: post views → profile views correlation
# LinkedIn doesn't provide per-post profile visits directly
# but provides profile views total per period
# Correlate: spike in profile views on day post went out = attribution

def estimate_linkedin_profile_visits(post_published_at: datetime,
                                      account: str) -> int:
    """
    Rough attribution: profile views on day of post minus baseline.
    Not perfect but directionally correct.
    """
    day_views = fetch_linkedin_profile_views(account, date=post_published_at.date())
    baseline_views = get_average_daily_profile_views(account, last_n_days=7)
    attributed_visits = max(0, day_views - baseline_views)
    return attributed_visits
```

**Add to PostAnalytics model:**
```python
profile_visits = Column(Integer, default=0)
website_clicks = Column(Integer, default=0)
```

---

## GAP 3.3 — Audience Demographic Quality Scoring

**The Problem:**
50 follows from Nigerian developers is worth more to Ahmad than 500 follows from irrelevant accounts. Current system treats all follows equally.

**The Solution:**

```python
# backend/analytics/audience_quality.py — NEW

TARGET_AUDIENCE_SIGNALS = {
    "keywords_in_bio": [
        "developer", "engineer", "founder", "startup", "tech",
        "nigeria", "africa", "abuja", "lagos", "software", "code",
        "indie", "saas", "build"
    ],
    "preferred_locations": ["nigeria", "ghana", "kenya", "africa", "abuja", "lagos"],
    "preferred_industries": ["technology", "software", "startups", "engineering"]
}

def score_follower_quality(follower_profile: dict) -> float:
    """
    Score how well a new follower matches Ahmad's target audience.
    Uses publicly available profile data.
    """
    score = 0.0
    bio = (follower_profile.get("biography", "") or "").lower()
    location = (follower_profile.get("location", "") or "").lower()

    # Bio keyword match
    keyword_matches = sum(1 for kw in TARGET_AUDIENCE_SIGNALS["keywords_in_bio"]
                          if kw in bio)
    score += keyword_matches * 0.2

    # Location relevance
    if any(loc in location for loc in TARGET_AUDIENCE_SIGNALS["preferred_locations"]):
        score += 0.5

    # Account activity (not a bot)
    follower_count = follower_profile.get("followers_count", 0)
    following_count = follower_profile.get("following_count", 0)
    post_count = follower_profile.get("post_count", 0)

    if post_count > 5 and follower_count > 10:  # not a brand new/bot account
        score += 0.3

    # Suspicious bot signals
    if following_count > 5000 and follower_count < 100:
        score = 0.0  # follow-unfollow bot pattern

    return min(score, 1.0)

def compute_post_audience_quality_score(new_followers: list[dict]) -> float:
    """Average quality score of followers gained from a post."""
    if not new_followers:
        return 0.0
    scores = [score_follower_quality(f) for f in new_followers]
    return sum(scores) / len(scores)
```

**Note:** Instagram's API limits follower data access. This works fully for the first 30 days on Instagram Basic Display API. For LinkedIn, follower demographic data is available via the `r_organization_social` scope on company pages.

---

# PART 4 — AHMAD-SPECIFIC COMPLETIONS

---

## GAP 4.1 — Whisper Vlog Transcription

**The Problem:**
AGENTS.md mentions "vlog transcript → repurposer" but there's no UI or endpoint for Ahmad to upload a video and get a transcript. This breaks the vlog content flow entirely.

**The Solution:**

```python
# backend/api/media_upload.py — NEW

import whisper
import tempfile
from pathlib import Path

# Search: "openai whisper python pip install" for local model
# or use OpenAI Whisper API (costs ~$0.006/minute of audio)
# Recommendation: local whisper model on Railway for zero cost

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny/base/small/medium

def transcribe_video(video_path: Path) -> str:
    """
    Transcribe a video file to text using Whisper.
    Runs locally on Railway — zero per-call cost.
    """
    model = whisper.load_model(WHISPER_MODEL_SIZE)
    result = model.transcribe(str(video_path))
    return result["text"]

@router.post("/api/media/upload-vlog")
async def upload_vlog(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Ahmad uploads a vlog video.
    Oybit transcribes it and generates platform-native content from the transcript.
    """
    # Save uploaded file
    upload_dir = Path("/tmp/oybit_uploads")
    upload_dir.mkdir(exist_ok=True)
    video_path = upload_dir / f"{uuid4()}{Path(file.filename).suffix}"

    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Transcribe + generate in background (can take 2-5 minutes)
    job_id = create_transcription_job(str(video_path))
    background_tasks.add_task(process_vlog_upload, video_path, job_id)

    return {"job_id": job_id, "status": "processing",
            "message": "Transcription started — check back in ~3 minutes"}

async def process_vlog_upload(video_path: Path, job_id: str):
    """Background task: transcribe → repurpose → queue drafts."""
    try:
        # Step 1: Transcribe
        update_job_status(job_id, "transcribing")
        transcript = transcribe_video(video_path)

        # Step 2: Repurpose to all platforms
        update_job_status(job_id, "generating_content")
        platform_posts = repurposer.repurpose_from_transcript(transcript)

        # Step 3: Create draft posts for each account
        for account, content in platform_posts.items():
            create_draft_post(account=account, content=content,
                              source="vlog_upload", source_job_id=job_id)

        update_job_status(job_id, "complete",
                          result={"post_count": len(platform_posts)})

        # Alert Ahmad via Telegram
        send_alert_to_ahmad(
            f"Vlog processed — {len(platform_posts)} drafts ready for approval"
        )

    except Exception as e:
        update_job_status(job_id, "failed", error=str(e))
        logger.error("Vlog processing failed",
                     extra={"job_id": job_id, "error": str(e)})
    finally:
        video_path.unlink(missing_ok=True)  # cleanup

@router.get("/api/media/vlog-status/{job_id}")
async def get_vlog_status(job_id: str):
    """Poll for transcription job status."""
    job = get_job(job_id)
    return {"job_id": job_id, "status": job.status, "result": job.result}
```

**Add to dashboard (frontend):**
- "Upload Vlog" button on dashboard home
- Drag-and-drop video file area
- Status polling with progress indicator
- "N drafts ready" notification when complete

**Add `whisper` to requirements.txt:**
```
openai-whisper==20231117    # pin exact version
```

---

## GAP 4.2 — Nyvora Product Event Webhooks

**The Problem:**
ColdSift gets a new paying customer. Volari Finance ships a new feature. OutreachBot hits a milestone. These are all post-worthy real events. There is no mechanism for other Nyvora products to signal Oybit.

**The Solution:**

```python
# backend/api/external_events.py — NEW

from pydantic import BaseModel
import hmac, hashlib

class ExternalEventPayload(BaseModel):
    product: str          # "coldsift" | "volari_finance" | "outreachbot" | "folio"
    event_type: str       # "new_user" | "first_payment" | "milestone" | "feature_shipped" | "bug_fixed"
    description: str      # human-readable description of what happened
    metrics: dict = {}    # optional: {"users": 10, "revenue": "$50"}
    urgency: str = "normal"  # "high" | "normal"
    signature: str        # HMAC-SHA256 signature for verification

NYVORA_WEBHOOK_SECRET = os.getenv("NYVORA_INTERNAL_WEBHOOK_SECRET")

@router.post("/api/events/external")
async def receive_external_event(payload: ExternalEventPayload):
    """
    Webhook endpoint for other Nyvora products to trigger content briefs.
    Protected by shared HMAC secret.
    """
    # Verify signature
    expected_sig = hmac.new(
        NYVORA_WEBHOOK_SECRET.encode(),
        f"{payload.product}:{payload.event_type}:{payload.description}".encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(payload.signature, expected_sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Create high-priority content brief
    brief = {
        "source": "external_product_event",
        "product": payload.product,
        "event_type": payload.event_type,
        "description": payload.description,
        "metrics": payload.metrics,
        "priority": "high" if payload.urgency == "high" else "normal",
        "bypass_mirofish": True,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Expand into structured content brief
    expanded = expand_product_event_brief(brief)

    # Inject into content queue
    queue_id = create_priority_brief(expanded)

    logger.info("External product event received",
                extra={"product": payload.product,
                        "event_type": payload.event_type,
                        "queue_id": queue_id})

    return {"status": "queued", "queue_id": queue_id}

def expand_product_event_brief(brief: dict) -> dict:
    """
    Use OpenRouter to expand a raw event into a structured content brief.
    Example: "ColdSift got first paying customer" →
    structured brief with angle, hook type, target accounts, etc.
    """
    prompt = f"""
    A real product event just happened. Turn this into a content brief.
    
    Product: {brief["product"]}
    Event: {brief["event_type"]}
    Description: {brief["description"]}
    Metrics: {brief.get("metrics", {})}
    
    Return JSON with:
    - headline: one punchy sentence about what happened
    - angle: what story angle to take
    - hook_type: consequence|mechanism|contradiction|story
    - target_accounts: list of ["linkedin","instagram_personal","instagram_brand","facebook"]
    - content_dna_element: which DNA element this naturally has
    - suggested_formats: list of post formats to generate
    
    Output ONLY valid JSON, no explanation.
    """
    response = call_openrouter({"messages": [{"role": "user", "content": prompt}],
                                 "max_tokens": 300})
    return json.loads(response["choices"][0]["message"]["content"])
```

**Add to ColdSift, Volari Finance, OutreachBot:**
```python
# In each Nyvora product — send webhook on key events
import hmac, hashlib, requests

def notify_oybit(event_type: str, description: str, metrics: dict = {}):
    secret = os.getenv("NYVORA_INTERNAL_WEBHOOK_SECRET")
    sig = hmac.new(
        secret.encode(),
        f"coldsift:{event_type}:{description}".encode(),
        hashlib.sha256
    ).hexdigest()

    requests.post(
        f"{OYBIT_API_URL}/api/events/external",
        json={
            "product": "coldsift",
            "event_type": event_type,
            "description": description,
            "metrics": metrics,
            "signature": sig
        },
        timeout=5
    )
```

**Add env var:** `NYVORA_INTERNAL_WEBHOOK_SECRET` — shared secret across all Nyvora products.

---

## GAP 4.3 — Ahmad's Voice Drift Detection

**The Problem:**
As Ahmad grows, evolves, and changes direction, his real voice will drift from the initial persona.md. The system currently only updates persona.md from engagement data, not from detecting that Ahmad himself sounds different.

**The Solution:**

```python
# backend/persona_engine/drift_detector.py — NEW

def detect_voice_drift(recent_manual_posts: list[str],
                        persona_path: Path) -> dict:
    """
    Compare Ahmad's recent manually-written posts against persona.md voice.
    If semantic distance is growing, trigger a voice recalibration.
    
    Called weekly by feedback_worker after collecting any manual posts.
    """
    if len(recent_manual_posts) < 3:
        return {"drift_detected": False, "reason": "insufficient data"}

    persona = persona_path.read_text(encoding='utf-8')

    prompt = f"""
    Compare these recent posts written by Ahmad against his stored persona.
    
    STORED PERSONA VOICE:
    {extract_voice_section(persona)}
    
    RECENT POSTS AHMAD WROTE MANUALLY:
    {chr(10).join(f"Post {i+1}: {p}" for i, p in enumerate(recent_manual_posts))}
    
    Analyze:
    1. Has the tone shifted? (more formal/casual, more/less technical)
    2. Are new topics emerging that aren't in the persona?
    3. Are old topics disappearing from his writing?
    4. Has the vocabulary changed?
    
    Return JSON:
    {{
        "drift_detected": true/false,
        "drift_severity": "none|minor|moderate|significant",
        "tone_shift": "description or null",
        "new_topics": ["topic1", "topic2"],
        "fading_topics": ["topic1"],
        "vocabulary_changes": "description or null",
        "recommended_updates": ["specific persona.md section update 1", ...]
    }}
    
    Output ONLY valid JSON.
    """

    response = call_openrouter({
        "messages": [{"role": "user", "content": prompt}],
        "model": OPENROUTER_DEEP_MODEL,  # use deeper model for nuance
        "max_tokens": 500
    })

    result = json.loads(response["choices"][0]["message"]["content"])

    if result["drift_detected"] and result["drift_severity"] in ["moderate", "significant"]:
        logger.warning("Voice drift detected",
                       extra={"severity": result["drift_severity"],
                               "tone_shift": result.get("tone_shift")})
        # Alert Ahmad
        send_alert_to_ahmad(
            f"Voice drift detected ({result['drift_severity']}). "
            f"Suggested persona updates ready for review. "
            f"Check dashboard → Persona → Drift Report."
        )
        # Save drift report for dashboard
        save_drift_report(result)

    return result
```

**Add drift report to dashboard persona page:**
- "Voice Drift Report" section showing detected changes
- "Accept suggested updates" button (applies recommended changes to persona.md)
- "Dismiss" button (marks as reviewed, no changes)

---

## GAP 4.4 — Nigerian Public Holidays and Cultural Calendar

**The Problem:**
Posting promotional content on a day of national tragedy or public holiday is tone-deaf. The system has no concept of Nigerian cultural context.

**The Solution:**

```python
# backend/intelligence/cultural_calendar.py — NEW

NIGERIAN_PUBLIC_HOLIDAYS = {
    "01-01": "New Year's Day",
    "04-18": "Good Friday",  # approximate — varies by year
    "04-21": "Easter Monday",  # approximate
    "05-01": "Workers Day",
    "06-12": "Democracy Day",
    "08-06": "Eid al-Adha",  # approximate — lunar calendar
    "10-01": "Independence Day",
    "10-25": "Eid al-Mawlid",  # approximate
    "12-25": "Christmas Day",
    "12-26": "Boxing Day",
}

# Ramadan: approximate dates — update annually
RAMADAN_2026 = {"start": "2026-02-18", "end": "2026-03-19"}

REDUCED_POSTING_DAYS = {
    "ramadan": "reduce posting frequency — not stop entirely",
    "exam_period_uniabuja": "Ahmad is a student — university exam periods",
}

def is_sensitive_posting_day(date: datetime.date) -> dict:
    """Check if a given date requires special posting consideration."""
    month_day = date.strftime("%m-%d")

    # Public holiday
    if month_day in NIGERIAN_PUBLIC_HOLIDAYS:
        return {
            "is_sensitive": True,
            "reason": f"Nigerian public holiday: {NIGERIAN_PUBLIC_HOLIDAYS[month_day]}",
            "recommendation": "pause_all"
        }

    # Ramadan
    ramadan_start = datetime.strptime(RAMADAN_2026["start"], "%Y-%m-%d").date()
    ramadan_end = datetime.strptime(RAMADAN_2026["end"], "%Y-%m-%d").date()
    if ramadan_start <= date <= ramadan_end:
        return {
            "is_sensitive": False,  # not a pause, just awareness
            "reason": "Ramadan period",
            "recommendation": "reduce_frequency"
        }

    return {"is_sensitive": False}

def apply_cultural_calendar_to_schedule(jobs: list) -> list:
    """
    Before dispatching scheduled posts, check cultural calendar.
    Pause or reduce posts on sensitive days.
    """
    filtered = []
    for job in jobs:
        scheduled_date = job.scheduled_at.date()
        sensitivity = is_sensitive_posting_day(scheduled_date)

        if sensitivity["is_sensitive"]:
            pause_job(job.id, reason=sensitivity["reason"])
            send_alert_to_ahmad(
                f"Posts paused for {scheduled_date}: {sensitivity['reason']}"
            )
        else:
            filtered.append(job)

    return filtered
```

**Add `EXAM_PERIODS` config that Ahmad updates each semester:**
```python
# In settings — Ahmad manually adds his exam periods
EXAM_PERIODS = [
    {"start": "2026-05-10", "end": "2026-05-25", "label": "Semester 2 exams"},
]
# During exam periods: switch all accounts to buffer-only mode
# (pre-approved buffer posts only, no new generation)
```

---

# PART 5 — LONG-TERM ARCHITECTURE

---

## GAP 5.1 — Waitlist Capture Mechanism

**The Problem:**
When Oybit gets attention (Ahmad hits 5k LinkedIn followers, shares what the tool is doing), people will want access. No mechanism to capture that interest.

**The Solution:**

```python
# backend/api/waitlist.py — NEW

class WaitlistEntry(Base):
    __tablename__ = "waitlist"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String, nullable=True)
    platform_source = Column(String)   # which platform they came from
    referral_post_id = Column(Integer, nullable=True)  # which post drove them
    signed_up_at = Column(DateTime, default=datetime.utcnow)
    notified_at = Column(DateTime, nullable=True)

@router.post("/waitlist")
async def join_waitlist(email: str, name: str = None,
                         source: str = "direct", post_id: int = None):
    """Public endpoint — no auth required."""
    entry = WaitlistEntry(
        email=email, name=name,
        platform_source=source,
        referral_post_id=post_id
    )
    db.add(entry)
    db.commit()
    return {"status": "joined", "position": db.query(WaitlistEntry).count()}

@router.get("/waitlist/count")
async def waitlist_count():
    """Public — Ahmad can show this in posts: '247 people waiting'."""
    return {"count": db.query(WaitlistEntry).count()}
```

**Add to dashboard:** Waitlist count card — "N people waiting for Oybit access"

**Add to posts:** When Ahmad posts about Oybit, include link to `oybit.nyvora.com/waitlist`. The link click → profile visit → waitlist signup funnel is the product's GTM in motion.

---

## GAP 5.2 — persona/_template.md Production-Ready Version

**The Problem:**
`persona/_template.md` is a placeholder. When Oybit opens to other users, this is what drives their entire onboarding. It needs to be production-ready.

**The Solution:**

```markdown
# [Brand Name] — Persona
# Generated by Oybit onboarding | Version: 1 | Created: [date]
# DO NOT EDIT manually unless you understand the full implications.
# Use the Oybit dashboard persona editor for safe edits.
# Sections marked [PROTECTED] are managed by the learning engine — manual edits will be overwritten.

---

## 1. Identity

**Brand name:** [FILL — from Stage 1 Q1]
**Tagline:** [FILL — from Stage 1 Q2]
**Mission:** [FILL — from Stage 1 Q3]
**Values:** [FILL — from Stage 1 Q4]
**Origin story:** [FILL — from Stage 1 Q5]
**We stand for:** [FILL — from Stage 1 Q6]
**We stand against:** [FILL — from Stage 1 Q7]

---

## 2. Voice & Tone

**Formality scale:** [1-10 from Stage 1 Q8]
**Primary language:** [from Stage 1 Q9]
**Reference voices:** [from Stage 1 Q10]

**Vocabulary always used:**
[from Stage 3 — tone deep dive]

**Vocabulary never used:**
[from Stage 3 — tone deep dive]

**Punctuation style:** [from Stage 3]
**Sentence length preference:** [short/medium/long/mixed — from Stage 3]
**Fragment tolerance:** [yes/no/sometimes — from Stage 3]
**Emoji policy:** [never/rare/moderate/frequent — from Stage 3]
**Humour style:** [none/dry/playful/self-deprecating — from Stage 3]

---

## 3. Audience

**Primary audience:** [from Stage 1 Q11]
**Age range:** [from Stage 1 Q12]
**Location:** [from Stage 1 Q13]
**Pain points:** [from Stage 1 Q14]
**Language they use:** [from Stage 1 Q15]
**What they come to us for:** [from Stage 1 Q16]
**What they never want to see:** [from Stage 1 Q17]

---

## 4. Content Pillars

| Pillar | Description | Weight |
|---|---|---|
| [from Stage 1 Q18] | [description] | [%] |
| [from Stage 1 Q19] | [description] | [%] |
| [from Stage 1 Q20] | [description] | [%] |
| [from Stage 1 Q21] | [description] | [%] |

**Hard stops — never post about:**
[from Stage 4 — content boundaries]

---

## 5. Per-Account Tone Modifiers

**Instagram personal:** [from Stage 1 Q22]
**Instagram brand:** [from Stage 1 Q23]
**LinkedIn:** [from Stage 1 Q24]
**Facebook:** [from Stage 1 Q25]

---

## 6. Competitive Landscape

**Key competitors:** [from Stage 1 Q26]
**How we differ:** [from Stage 1 Q27]
**Narrative we fight against:** [from Stage 1 Q28]

---

## 7. Engagement Style

**Reply tone:** [from Stage 6 Q1]
**Handling praise:** [from Stage 6 Q2]
**Handling criticism:** [from Stage 6 Q3]
**Handling debate:** [from Stage 6 Q4]
**Handling spam:** [from Stage 6 Q5]

---

## 8. Visual Identity

**Primary color:** [hex — from Stage 1 Q29]
**Secondary color:** [hex — from Stage 1 Q30]
**Primary font:** [font name]
**Logo URL:** [if provided]
**Visual style:** [minimal/bold/playful/corporate/technical]

---

## 9. Performance Memory [PROTECTED]

_Managed exclusively by the learning engine. Do not edit manually._

**Top content types:**

| Account | Best format | Best pillar | Avg score |
|---|---|---|---|
| instagram_personal | [auto-filled] | [auto-filled] | [auto-filled] |
| instagram_brand | [auto-filled] | [auto-filled] | [auto-filled] |
| linkedin | [auto-filled] | [auto-filled] | [auto-filled] |
| facebook | [auto-filled] | [auto-filled] | [auto-filled] |

**Engagement benchmarks:**

| Account | Followers | Avg reach | Avg score |
|---|---|---|---|
| instagram_personal | [auto-filled] | [auto-filled] | [auto-filled] |

**Strategy history:**

| Version | Date | Trigger | Change |
|---|---|---|---|
| 1 | [creation date] | Initial | Baseline from onboarding |

**Current strategy focus:** [auto-filled by learning engine]
**Next rotation check:** [auto-filled]
```

---

## GAP 5.3 — Onboarding Simulation Engine Public Content Mode

**The Problem:**
Stage 2 simulation pulls real posts from user's target platforms to show as scenarios. But this requires platform API access — which requires connected accounts — which requires completing onboarding first. Chicken and egg.

**The Solution:**

```python
# backend/onboarding/sim_engine.py — add public content mode

def get_simulation_scenarios(stage_1_answers: dict,
                              connected_accounts: list) -> list:
    """
    If accounts are connected: pull real trending posts (personalized)
    If accounts NOT connected: use curated public content bank (generic but functional)
    """
    if connected_accounts:
        return fetch_personalized_scenarios(stage_1_answers, connected_accounts)
    else:
        return fetch_public_content_bank_scenarios(stage_1_answers)

def fetch_public_content_bank_scenarios(answers: dict) -> list:
    """
    Pre-curated scenario bank — doesn't require platform auth.
    Organized by niche/interest category.
    Updated monthly by Oybit team (or by Ahmad for his own use).
    """
    niche = extract_niche_from_answers(answers)
    base_scenarios = load_scenario_bank(niche)

    # Supplement with Reddit public API (no auth required)
    reddit_posts = fetch_reddit_public_posts(
        subreddits=get_niche_subreddits(niche),
        sort="hot",
        limit=10
    )

    for post in reddit_posts:
        base_scenarios.append({
            "platform": "reddit",
            "scenario_type": "trending_post_reaction",
            "shown_content": post["title"] + "\n\n" + post.get("selftext", ""),
            "source": "reddit_public"
        })

    return base_scenarios[:30]  # always return exactly 30
```

**Build `backend/onboarding/scenario_bank/` folder:**
```
scenario_bank/
├── tech_founder.json       # scenarios for tech founders
├── developer.json          # scenarios for developers
├── african_startup.json    # Africa-specific startup scenarios
├── indie_hacker.json       # indie hacker scenarios
└── general.json            # fallback for any niche
```

Each JSON file contains 30+ pre-written scenarios that work without platform API access.

---

# PART 6 — CONTENT QUALITY FINAL FIXES

---

## GAP 6.1 — Cross-Platform Content Variation Enforcement

**The Problem:**
If LinkedIn and Instagram personal both get a post about the same topic on the same day, they'll look identical to anyone who follows Ahmad on both platforms. Feels robotic, breaks authenticity.

**The Solution:**

```python
# backend/content/variation_enforcer.py — NEW

MIN_VARIATION_SCORE = 0.4  # posts must differ by at least 40%

def enforce_cross_platform_variation(posts_batch: dict) -> dict:
    """
    For posts about the same topic going to multiple platforms same day:
    Ensure they're different enough to not feel duplicated.
    
    posts_batch = {"linkedin": "post text", "instagram_personal": "post text"}
    """
    from sentence_transformers import SentenceTransformer
    import numpy as np

    model = SentenceTransformer('all-MiniLM-L6-v2')
    accounts = list(posts_batch.keys())
    texts = list(posts_batch.values())

    if len(texts) < 2:
        return posts_batch

    embeddings = model.encode(texts)

    # Check all pairs
    regenerate = []
    for i in range(len(accounts)):
        for j in range(i+1, len(accounts)):
            similarity = float(np.dot(embeddings[i], embeddings[j]))
            if similarity > (1 - MIN_VARIATION_SCORE):
                # Too similar — mark one for regeneration with variation instruction
                regenerate.append({
                    "account": accounts[j],
                    "similar_to": accounts[i],
                    "similarity": similarity
                })

    for item in regenerate:
        logger.warning("Cross-platform content too similar — regenerating",
                        extra=item)
        posts_batch[item["account"]] = regenerate_with_variation_instruction(
            original=posts_batch[item["similar_to"]],
            account=item["account"],
            instruction=f"This is for {item['account']}. "
                        f"The {item['similar_to']} version was: '{posts_batch[item['similar_to']][:100]}...'"
                        f"Write a substantially different version — different angle, "
                        f"different hook, different examples. Same topic, different take."
        )

    return posts_batch

# Also enforce 48-hour topic exclusivity between accounts:
def check_topic_exclusivity(topic: str, accounts: list,
                             db: Session, window_hours: int = 48) -> list:
    """
    Same topic can't appear on 2 accounts within 48 hours.
    Returns list of accounts where the topic is blocked.
    """
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    blocked = []
    for account in accounts:
        recent_same_topic = db.query(Post).filter(
            Post.account == account,
            Post.topic_pillar == topic,
            Post.published_at >= cutoff
        ).first()
        if recent_same_topic:
            blocked.append(account)
    return blocked
```

---

## GAP 6.2 — LinkedIn First Line Never Starts With "I"

**The Problem:**
LinkedIn's algorithm is known to penalize posts that begin with "I". This is a widely documented pattern in the LinkedIn creator community. Brand Voice Guardian doesn't currently check for this.

**The Solution:**

```python
# backend/brand_voice_guardian/checker.py — add LinkedIn-specific checks

def check_linkedin_specific_rules(text: str) -> dict:
    """
    LinkedIn-specific rules beyond general Brand Voice Guardian checks.
    """
    issues = []

    # Never start with "I"
    first_word = text.strip().split()[0] if text.strip() else ""
    if first_word.lower() == "i":
        issues.append({
            "rule": "linkedin_no_start_with_I",
            "severity": "warning",
            "suggestion": f"Don't start with 'I'. Rewrite opening: '{text[:60]}...'"
        })

    # Never start with a question
    if text.strip().startswith("?") or text.strip().split()[0].endswith("?"):
        issues.append({
            "rule": "linkedin_no_question_opener",
            "severity": "warning",
            "suggestion": "LinkedIn algorithm penalizes question openers. Start with a statement."
        })

    # Emoji count (max 3 for LinkedIn)
    import emoji
    emoji_count = emoji.emoji_count(text)
    if emoji_count > 3:
        issues.append({
            "rule": "linkedin_emoji_limit",
            "severity": "warning",
            "suggestion": f"Too many emoji ({emoji_count}). Max 3 for LinkedIn algorithm."
        })

    # Hashtag count (max 5)
    hashtag_count = len(re.findall(r'#\w+', text))
    if hashtag_count > 5:
        issues.append({
            "rule": "linkedin_hashtag_limit",
            "severity": "error",
            "suggestion": f"Too many hashtags ({hashtag_count}). Max 5 for LinkedIn."
        })

    return {
        "platform": "linkedin",
        "issues": issues,
        "passes": len([i for i in issues if i["severity"] == "error"]) == 0
    }
```

---

## GAP 6.3 — Instagram Reel Caption 125-Char Hook Rule

**The Problem:**
Instagram truncates Reel captions at 125 chars in the feed. Everything after requires a tap. If the hook isn't in the first 125 chars, the post is effectively hookless in the feed.

**The Solution:**

```python
# backend/content/platform_rules.py — add to Instagram Reel rules

INSTAGRAM_REEL_CAPTION_VISIBLE_CHARS = 125

def validate_reel_caption_hook(caption: str) -> dict:
    """
    First 125 chars must contain the hook.
    Everything after is secondary.
    """
    visible_portion = caption[:INSTAGRAM_REEL_CAPTION_VISIBLE_CHARS]

    # Check if visible portion ends mid-sentence
    if len(caption) > INSTAGRAM_REEL_CAPTION_VISIBLE_CHARS:
        # Make sure visible portion is a complete thought
        last_sentence_end = max(
            visible_portion.rfind('.'),
            visible_portion.rfind('!'),
            visible_portion.rfind('?'),
            visible_portion.rfind('\n')
        )
        if last_sentence_end < 50:  # no sentence ending in first 50 chars
            return {
                "passes": False,
                "issue": f"Hook may be cut off. Visible: '{visible_portion}'",
                "suggestion": "Put the strongest statement in first 125 chars"
            }

    return {"passes": True, "visible_hook": visible_portion}
```

**Add this check to Brand Voice Guardian for Reel post type:**
```python
if post_type == PostType.REEL:
    reel_check = validate_reel_caption_hook(text)
    if not reel_check["passes"]:
        return near_pass(edit_suggestion=reel_check["suggestion"])
```

---

# PART 7 — INFRASTRUCTURE FINAL PIECES

---

## GAP 7.1 — Worker Heartbeat System

**The Problem:**
No way to know if a worker silently died 3 days ago. MiroFish could have stopped running and nobody knows.

**The Solution:**

```python
# backend/db/models.py — add WorkerHeartbeat

class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    worker_name = Column(String, primary_key=True)
    last_started_at = Column(DateTime)
    last_completed_at = Column(DateTime, nullable=True)
    last_status = Column(String)  # running|completed|failed
    last_error = Column(Text, nullable=True)
    run_count = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)
```

**Add to EVERY worker file:**
```python
# workers/mirofish_worker.py — add heartbeat calls

from backend.db.models import WorkerHeartbeat

def update_heartbeat(status: str, error: str = None):
    with SessionLocal() as db:
        hb = db.query(WorkerHeartbeat).filter_by(
            worker_name="mirofish_worker"
        ).first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="mirofish_worker")
            db.add(hb)
        hb.last_status = status
        if status == "running":
            hb.last_started_at = datetime.utcnow()
            hb.run_count = (hb.run_count or 0) + 1
        elif status == "completed":
            hb.last_completed_at = datetime.utcnow()
            hb.consecutive_failures = 0
        elif status == "failed":
            hb.last_error = error
            hb.consecutive_failures = (hb.consecutive_failures or 0) + 1
        db.commit()

# In worker main():
update_heartbeat("running")
try:
    run_worker_logic()
    update_heartbeat("completed")
except Exception as e:
    update_heartbeat("failed", error=str(e))
    # Alert Ahmad if 3+ consecutive failures
    failures = get_consecutive_failures("mirofish_worker")
    if failures >= 3:
        send_alert_to_ahmad(
            f"mirofish_worker has failed {failures} times in a row. "
            f"Last error: {str(e)[:200]}"
        )
```

---

## GAP 7.2 — setup_graphrag.py Script

```python
# scripts/setup_graphrag.py
"""
Run this ONCE before first MiroFish run.
Creates GraphRAG project structure and configures it to use OpenRouter.
Run: python scripts/setup_graphrag.py
"""

import subprocess, os, shutil
from pathlib import Path

GRAPHRAG_DIR = Path("backend/intelligence/mirofish/graphrag_project")

def setup():
    print("Setting up GraphRAG...")

    # Create directory
    GRAPHRAG_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize GraphRAG project
    result = subprocess.run(
        ["graphrag", "init", "--root", str(GRAPHRAG_DIR)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"GraphRAG init failed: {result.stderr}")
        print("GraphRAG may not be installed. Run: pip install graphrag")
        return False

    # Configure to use OpenRouter instead of OpenAI
    settings_path = GRAPHRAG_DIR / "settings.yaml"
    if settings_path.exists():
        content = settings_path.read_text()
        # Replace OpenAI config with OpenRouter
        content = content.replace(
            "model: gpt-4-turbo-preview",
            f"model: {os.getenv('OPENROUTER_DEFAULT_MODEL', 'meta-llama/llama-4-scout')}"
        )
        content = content.replace(
            "api_base: https://api.openai.com/v1",
            "api_base: https://openrouter.ai/api/v1"
        )
        settings_path.write_text(content)

    # Set GraphRAG API key to OpenRouter key
    env_path = GRAPHRAG_DIR / ".env"
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    env_path.write_text(f"GRAPHRAG_API_KEY={openrouter_key}\n")

    print("GraphRAG setup complete.")
    print(f"Project directory: {GRAPHRAG_DIR}")
    return True

if __name__ == "__main__":
    success = setup()
    exit(0 if success else 1)
```

---

## GAP 7.3 — bootstrap_pattern_db.py Script

```python
# scripts/bootstrap_pattern_db.py
"""
Seed PatternDB from Ahmad's existing LinkedIn post history.
Run ONCE before first Oybit post goes out.
This prevents the scoring system from being blind on day one.

Ahmad already has 30 LinkedIn posts with impression data.
Use them as PatternDB seed data.

Run: python scripts/bootstrap_pattern_db.py
"""

import os, sys
sys.path.insert(0, os.path.abspath("."))

from backend.db.session import SessionLocal
from backend.db.models import PatternDB, Post, PostAnalytics
from backend.content.generator import call_openrouter
import json

def classify_existing_post(post_text: str) -> dict:
    """Use AI to classify hook_type, topic_pillar, emotional_tone of existing post."""
    prompt = f"""
    Classify this LinkedIn post:
    
    "{post_text[:500]}"
    
    Return JSON:
    {{
        "hook_type": "consequence|mechanism|contradiction|story|question|number|personal_incident",
        "topic_pillar": "technical_systems|building_in_public|african_founder|product_update|personal_grind",
        "emotional_tone": "consequence|insight|contradiction|celebration|frustration",
        "estimated_engagement_tier": "high|medium|low"
    }}
    
    Output ONLY valid JSON.
    """
    response = call_openrouter({"messages": [{"role": "user", "content": prompt}], "max_tokens": 150})
    return json.loads(response["choices"][0]["message"]["content"])

def bootstrap_from_linkedin_history():
    """
    Fetches Ahmad's existing LinkedIn posts and their impression data.
    Creates PatternDB seed records.
    """
    print("Bootstrapping PatternDB from LinkedIn history...")

    # Fetch Ahmad's existing posts from LinkedIn API
    from backend.publishers.linkedin import fetch_my_posts
    existing_posts = fetch_my_posts(limit=30)

    with SessionLocal() as db:
        for post in existing_posts:
            classification = classify_existing_post(post["text"])

            # Create or update PatternDB record
            combo_key = f"{classification['hook_type']}:{classification['topic_pillar']}:{classification['emotional_tone']}"

            existing_pattern = db.query(PatternDB).filter_by(
                account="linkedin",
                hook_type=classification["hook_type"],
                topic_pillar=classification["topic_pillar"],
            ).first()

            impressions = post.get("impressions", 0)
            estimated_score = impressions / 10  # rough engagement estimate from impressions

            if existing_pattern:
                # Update average
                total = existing_pattern.avg_engagement_score * existing_pattern.post_count
                existing_pattern.post_count += 1
                existing_pattern.avg_engagement_score = (total + estimated_score) / existing_pattern.post_count
            else:
                new_pattern = PatternDB(
                    account="linkedin",
                    hook_type=classification["hook_type"],
                    topic_pillar=classification["topic_pillar"],
                    emotional_tone=classification["emotional_tone"],
                    format="text",
                    avg_engagement_score=estimated_score,
                    post_count=1,
                )
                db.add(new_pattern)

        db.commit()

    print(f"PatternDB bootstrapped with {len(existing_posts)} historical posts.")
    print("The scoring system is no longer blind on day one.")

if __name__ == "__main__":
    bootstrap_from_linkedin_history()
```

---

# PART 8 — FINAL ENVIRONMENT VARIABLES

Add these missing env vars to Railway/Render — not in any previous doc:

```bash
# Follow strategy (off by default)
FOLLOW_STRATEGY_ENABLED=false
MAX_FOLLOWS_PER_DAY=50
UNFOLLOW_AFTER_DAYS=7

# Whisper transcription
WHISPER_MODEL_SIZE=base           # tiny/base/small — base is best free/cost tradeoff

# Nyvora product integration
NYVORA_INTERNAL_WEBHOOK_SECRET=   # shared secret for product-to-Oybit webhooks
OYBIT_API_URL=https://your-railway-url.railway.app  # used by other Nyvora products

# Ahmad's personal Telegram chat ID (for alerts TO Ahmad, not publishing)
TELEGRAM_AHMAD_CHAT_ID=           # get this from @userinfobot on Telegram

# Oybit frontend URL (for CORS)
FRONTEND_URL=https://oybit.nyvora.com

# Cultural calendar
EXAM_PERIOD_START_1=2026-05-10
EXAM_PERIOD_END_1=2026-05-25

# LinkedIn seed accounts for comment opportunities (comma-separated URNs)
LINKEDIN_NICHE_SEED_ACCOUNTS=

# Instagram seed accounts for follow strategy (comma-separated usernames)
INSTAGRAM_NICHE_SEED_ACCOUNTS=

# Waitlist
OYBIT_WAITLIST_ENABLED=true

# YouTube (missing from previous docs)
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=

# Facebook Personal (for group posting)
FACEBOOK_PERSONAL_TOKEN=
FACEBOOK_TARGET_GROUPS=          # comma-separated group IDs Ahmad has joined

# LinkedIn groups Ahmad is in (comma-separated URNs)
LINKEDIN_TARGET_GROUPS=
```

---

# PART 9 — FINAL INTEGRATION TEST ADDITIONS

Add these to the `test_full_pipeline.py` integration test:

```python
# Additional checks for GAPS_FINAL coverage:

Step 13 — LinkedIn poll generation
  Check: poll generated for poll-appropriate brief
  Check: poll payload has correct structure (question + 2-4 options + duration)
  Check: option length <= 30 chars each, question <= 140 chars

Step 14 — Story scheduling after Reel
  Check: story job automatically created 30min after Reel is scheduled
  Check: story type is "link_cta"

Step 15 — Cross-platform variation
  Check: two posts about same topic for different accounts have < 0.6 similarity score
  Check: topic exclusivity window blocks same topic on two accounts within 48h

Step 16 — Cultural calendar
  Check: post scheduled on Nigerian public holiday is paused and alert sent
  Check: post NOT on holiday proceeds normally

Step 17 — Voice drift detection
  Check: drift_detector returns drift_detected=False for posts consistent with persona
  Check: drift_detector returns drift_detected=True for deliberately inconsistent test posts

Step 18 — External event webhook
  Check: POST /api/events/external with valid signature creates priority brief
  Check: POST /api/events/external with invalid signature returns 403

Step 19 — Vlog transcription
  Check: POST /api/media/upload-vlog with test video returns job_id
  Check: GET /api/media/vlog-status/{job_id} returns status (processing or complete)

Step 20 — LinkedIn first-line "I" check
  Check: "I built something today" fails Brand Voice Guardian for LinkedIn
  Check: "Built something today" passes

Step 21 — Reel caption hook check
  Check: Caption with hook in first 125 chars passes
  Check: Caption with only generic text in first 125 chars fails with suggestion
```

---

*All three gap files together (OYBIT_GAP_SOLUTIONS.md + GAPS_AND_FIXES.md + GAPS_FINAL.md) cover the complete known gap surface for Oybit Phase 0. Discovery gaps will emerge from real usage and be addressed iteratively.*
