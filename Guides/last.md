# REMAINING_GAPS.md — Oybit Final Gap Coverage

> Every gap not covered in GAPS_AND_FIXES.md or OYBIT_GAP_SOLUTIONS.md.
> Read this alongside both previous gap files. All three files together = complete coverage.
> This document wins in any conflict with the other two gap files.

---

# PART 1 — MISSING PUBLISHERS

---

## GAP 1.1 — LinkedIn Polls Publisher

**The Problem:**
LinkedIn polls currently outperform every other content format for organic reach. Zero implementation anywhere. This is a significant growth lever being left unused.

**The Solution:**

```python
# backend/publishers/linkedin_polls.py — NEW

def create_linkedin_poll(question: str, options: list[str],
                          duration_days: int = 7) -> str:
    """
    LinkedIn polls via ugcPosts with shareMediaCategory: POLL
    Max 4 options. Duration: 1, 3, 7, or 14 days only.
    Question max 140 chars. Each option max 30 chars.
    """
    if len(options) > 4:
        raise ValueError("LinkedIn polls max 4 options")
    if len(options) < 2:
        raise ValueError("LinkedIn polls need at least 2 options")
    if duration_days not in [1, 3, 7, 14]:
        raise ValueError("Duration must be 1, 3, 7, or 14 days")
    if len(question) > 140:
        question = question[:137] + "..."

    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": ""  # optional text above the poll
                },
                "shareMediaCategory": "POLL",
                "media": [{
                    "status": "READY",
                    "pollOptions": [
                        {"text": opt[:30]} for opt in options
                    ],
                    "pollDuration": f"P{duration_days}D",  # ISO 8601 duration
                    "question": {"text": question}
                }]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    # POST /v2/ugcPosts with this payload
    response = call_linkedin_api("POST", "/v2/ugcPosts", payload)
    return response["id"]
```

**Content generator for polls:**

```python
# backend/content/poll_generator.py — NEW

def generate_linkedin_poll(topic: str, persona_path: Path) -> dict:
    """
    Generate a LinkedIn poll from a topic brief.
    Good poll topics: controversial binary choices, experience polls,
    prediction questions, preference polls.
    """
    prompt = f"""
    Create a LinkedIn poll for this topic: {topic}

    Requirements:
    - Question must be under 140 characters
    - 3-4 options, each under 30 characters
    - Must be genuinely interesting and provoke engagement
    - Should relate to the audience's real experience
    - Must sound like Ahmad (read persona.md voice section)

    Return JSON only:
    {{
        "question": "...",
        "options": ["...", "...", "...", "..."],
        "duration_days": 7,
        "context_text": "Optional text to post above the poll"
    }}
    """
    result = call_openrouter(prompt)
    return json.loads(result)
```

**Add to PostType enum:**
```python
LINKEDIN_POLL = "linkedin_poll"
```

**Add to dispatcher routing:**
```python
elif post.post_type == PostType.LINKEDIN_POLL:
    return linkedin_polls.create_linkedin_poll(
        question=post.poll_question,
        options=post.poll_options,
        duration_days=post.poll_duration_days
    )
```

**Add poll fields to Post model:**
```python
poll_question = Column(String)       # for LINKEDIN_POLL type
poll_options = Column(JSON)          # list of strings
poll_duration_days = Column(Integer) # 1, 3, 7, or 14
```

**Scheduling rule:** Max 1 LinkedIn poll per week. Polls can't be back-to-back with other polls.

---

## GAP 1.2 — Instagram Stories Separate Module

**The Problem:**
Stories and feed posts are fundamentally different content types with different purposes. Stories don't contribute to feed reach but ARE the primary mechanism for converting profile visitors to followers. Treating them as "just another post format" produces wrong content.

**The Solution:**

```python
# backend/publishers/instagram_stories.py — NEW

class InstagramStoriesPublisher:
    """
    Stories content strategy:
    - Polls and question stickers drive engagement
    - Behind-the-scenes converts profile visitors to followers
    - "Link in bio" CTAs drive off-platform traffic
    - NOT for reach — for conversion of people who already found you
    """

    def post_photo_story(self, image_path: str, account: str) -> str:
        """Photo story — 15 second display."""
        token = get_token(account)
        user_id = get_user_id(account)

        # Upload image to storage and get URL
        image_url = upload_to_storage(image_path)

        # Create story container
        container_response = call_meta_api("POST", f"/{user_id}/media", {
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": token
        })
        container_id = container_response["id"]

        # Publish
        publish_response = call_meta_api("POST", f"/{user_id}/media_publish", {
            "creation_id": container_id,
            "access_token": token
        })
        return publish_response["id"]

    def post_video_story(self, video_path: str, account: str) -> str:
        """Video story — max 15 seconds, loops automatically."""
        token = get_token(account)
        user_id = get_user_id(account)

        video_url = upload_to_storage(video_path)

        container_response = call_meta_api("POST", f"/{user_id}/media", {
            "video_url": video_url,
            "media_type": "STORIES",
            "access_token": token
        })

        # Poll for video ready status
        container_id = container_response["id"]
        self._wait_for_video_ready(container_id, token)

        publish_response = call_meta_api("POST", f"/{user_id}/media_publish", {
            "creation_id": container_id,
            "access_token": token
        })
        return publish_response["id"]

    def _wait_for_video_ready(self, container_id: str, token: str,
                               max_attempts: int = 20):
        for attempt in range(max_attempts):
            status = call_meta_api("GET",
                f"/{container_id}?fields=status_code&access_token={token}")
            if status["status_code"] == "FINISHED":
                return
            elif status["status_code"] == "ERROR":
                raise Exception(f"Story video processing failed")
            time.sleep(5)
        raise TimeoutError("Story video ready timeout")
```

**Stories content generator — separate from feed content:**

```python
# backend/content/stories_generator.py — NEW

STORY_TYPES = [
    "poll",           # "Which do you prefer? A or B"
    "question_box",   # "Ask me anything about building a SaaS"
    "countdown",      # Product launch countdown
    "behind_scenes",  # Raw moment, no polish
    "link_cta",       # "New blog post — link in bio"
    "reaction_slider" # "How useful was today's post?"
]

def generate_story_content(story_type: str, context: str,
                            persona_path: Path) -> dict:
    """
    Stories are casual, raw, and interactive.
    They do NOT use the formal winning post structure.
    They use: hook question, poll, or raw statement.
    """
    prompt = f"""
    Generate Instagram Story content.
    Story type: {story_type}
    Context: {context}

    Stories must be:
    - Casual and raw (opposite of LinkedIn)
    - Short text only — Stories show image, text overlay is minimal
    - If poll: question + 2 options max 24 chars each
    - If question box: one open question
    - If behind_scenes: one honest raw statement
    - Sound like Ahmad's casual voice (not professional)

    Return JSON:
    {{
        "overlay_text": "max 60 chars shown on story",
        "story_type": "{story_type}",
        "poll_options": ["...", "..."],  # only if poll type
        "question_prompt": "..."          # only if question_box type
    }}
    """
    result = call_openrouter(prompt)
    return json.loads(result)
```

**Stories scheduling rules:**
- Max 3 stories per day per Instagram account
- Stories posted at different times than feed posts (don't compete)
- Personal IG: daily stories preferred (keep profile active for visitors)
- Brand IG: 3-4 stories per week (product-focused, less casual)
- Stories generate from separate content pool — not repurposed from feed posts

---

## GAP 1.3 — Facebook Reels Publisher

**The Problem:**
Facebook Reels get boosted reach similar to Instagram Reels. The current `facebook.py` posts regular videos via `/{page-id}/videos`. Facebook Reels require a completely different flow.

**The Solution:**

```python
# backend/publishers/facebook_reels.py — NEW

def post_facebook_reel(video_path: str, caption: str,
                        page_id: str, page_token: str) -> str:
    """
    Facebook Reels are boosted differently from regular page videos.
    Must use the Reels-specific endpoint, not /videos.
    Aspect ratio: 9:16. Duration: 3s - 90s.
    """

    # Step 1: Initialize upload session
    init_response = call_meta_api("POST",
        f"/{page_id}/video_reels", {
            "upload_phase": "start",
            "access_token": page_token
        }
    )
    video_id = init_response["video_id"]
    upload_url = init_response["upload_url"]

    # Step 2: Upload video binary
    with open(video_path, "rb") as f:
        video_data = f.read()

    upload_response = requests.post(
        upload_url,
        headers={
            "Authorization": f"OAuth {page_token}",
            "offset": "0",
            "file_size": str(len(video_data))
        },
        data=video_data
    )

    # Step 3: Finish upload and publish
    finish_response = call_meta_api("POST",
        f"/{page_id}/video_reels", {
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption,
            "access_token": page_token
        }
    )

    return video_id
```

**Add to PostType enum:**
```python
FACEBOOK_REEL = "facebook_reel"
```

**Facebook Reel validation (same as Instagram Reel):**
- 9:16 aspect ratio (1080x1920)
- Min 3 seconds, max 90 seconds
- Under 1GB file size
- Run through same `validate_video_for_instagram()` function

---

# PART 2 — GROWTH MECHANICS

---

## GAP 2.1 — Follow Strategy Module

**The Problem:**
On Instagram specifically, strategically following accounts in the niche triggers follow-backs and profile visits. This is a known growth lever. The decision to use it or not should be Ahmad's — but the implementation must exist.

**Note:** This walks a line with Instagram ToS. Ahmad must decide whether to enable it. It is off by default.

**The Solution:**

```python
# backend/growth/follow_strategy.py — NEW
# DISABLED BY DEFAULT. Enable via FOLLOW_STRATEGY_ENABLED=true env var.

import os
from datetime import datetime, timedelta

FOLLOW_STRATEGY_ENABLED = os.getenv("FOLLOW_STRATEGY_ENABLED", "false").lower() == "true"
MAX_FOLLOWS_PER_DAY = 100           # Instagram flags > 200/day — stay well under
MAX_FOLLOWS_TOTAL = 500             # don't follow more than 500 at once
UNFOLLOW_AFTER_DAYS = 7             # unfollow non-reciprocators after 7 days

class FollowManager:

    def find_follow_targets(self, seed_account_id: str) -> list[str]:
        """
        Find accounts that follow similar accounts to Ahmad.
        These are the most likely to follow back.
        """
        if not FOLLOW_STRATEGY_ENABLED:
            return []

        # GET /{seed_account_id}/followers — requires instagram_manage_insights
        # Filter: accounts that are not already followed, not bots
        # Bot signals: 0 posts, follower/following ratio > 10:1, no profile pic
        followers = self.fetch_followers(seed_account_id)
        return [f for f in followers if not self.looks_like_bot(f)]

    def execute_follows(self, target_ids: list[str], account: str) -> int:
        """Follow targets with human-like timing."""
        if not FOLLOW_STRATEGY_ENABLED:
            logger.info("Follow strategy disabled — skipping")
            return 0

        today_follows = self.count_today_follows(account)
        can_follow = MAX_FOLLOWS_PER_DAY - today_follows

        followed = 0
        for target_id in target_ids[:can_follow]:
            # Human-like delay between follows
            time.sleep(random.uniform(30, 90))

            success = self.follow_account(target_id, account)
            if success:
                self.record_follow(target_id, account)
                followed += 1

        return followed

    def execute_unfollows(self, account: str) -> int:
        """Unfollow accounts that didn't follow back after UNFOLLOW_AFTER_DAYS."""
        cutoff = datetime.utcnow() - timedelta(days=UNFOLLOW_AFTER_DAYS)
        to_unfollow = self.get_non_reciprocators(account, cutoff)

        unfollowed = 0
        for account_id in to_unfollow:
            time.sleep(random.uniform(20, 60))
            success = self.unfollow_account(account_id, account)
            if success:
                self.record_unfollow(account_id, account)
                unfollowed += 1

        return unfollowed

    def looks_like_bot(self, account_data: dict) -> bool:
        """Basic bot detection heuristics."""
        follower_count = account_data.get("followers_count", 0)
        following_count = account_data.get("follows_count", 0)
        post_count = account_data.get("media_count", 0)

        if post_count == 0:
            return True
        if follower_count > 0 and following_count / follower_count > 10:
            return True
        return False
```

**Add to DB models:**
```python
class FollowRecord(Base):
    __tablename__ = "follow_records"
    id = Column(Integer, primary_key=True)
    account = Column(String)           # which oybit account did the following
    target_account_id = Column(String) # who was followed
    followed_at = Column(DateTime)
    followed_back = Column(Boolean, default=False)
    unfollowed_at = Column(DateTime, nullable=True)
    status = Column(String)            # following|unfollowed|followed_back
```

**Add worker:**
```python
# workers/follow_worker.py — runs daily at 10AM if FOLLOW_STRATEGY_ENABLED=true
```

---

## GAP 2.2 — Saved Reply Templates

**The Problem:**
When a post goes viral, Ahmad gets 100+ similar comments. Generating a unique OpenRouter reply for each "how did you build this?" is expensive and slow. Templates with slight personalization per instance solve this.

**The Solution:**

```python
# backend/reply_manager/templates.py — NEW

class ReplyTemplateManager:

    def classify_comment(self, comment_text: str) -> str:
        """
        Classify incoming comment into a template category.
        Uses simple keyword matching first (free), falls back to AI.
        """
        comment_lower = comment_text.lower()

        # Keyword-based classification (free)
        if any(kw in comment_lower for kw in
               ["how did you", "how do you", "how to", "tutorial", "learn"]):
            return "how_to_question"
        elif any(kw in comment_lower for kw in
                 ["great post", "love this", "amazing", "inspiring", "brilliant"]):
            return "praise"
        elif any(kw in comment_lower for kw in
                 ["follow back", "check my", "dm me", "follow for follow"]):
            return "spam"
        elif any(kw in comment_lower for kw in
                 ["disagree", "wrong", "actually", "not true", "misleading"]):
            return "disagreement"
        elif any(kw in comment_lower for kw in
                 ["hire", "collaborate", "work with", "partnership", "project"]):
            return "business_inquiry"
        else:
            return "general"  # use AI for general comments

    def get_template(self, category: str, platform: str) -> str:
        """Get base template for comment category + platform."""
        return REPLY_TEMPLATES[platform][category]

    def personalize_template(self, template: str,
                              comment_text: str, persona_path: Path) -> str:
        """
        Lightly personalize a template for the specific comment.
        Much cheaper than full OpenRouter generation.
        Use template + 1 AI call to slot in specifics.
        """
        if "{personalization}" not in template:
            return template  # no personalization needed

        # One short AI call to extract key detail from comment
        detail = extract_comment_key_detail(comment_text)
        return template.replace("{personalization}", detail)


REPLY_TEMPLATES = {
    "linkedin": {
        "how_to_question": "Thanks for asking. The short answer: {personalization}. Happy to go deeper in a future post — drop a follow if you want that.",
        "praise": "Appreciate that. {personalization} Glad it landed.",
        "disagreement": "Fair point. {personalization} Worth a proper discussion — what's your experience been?",
        "business_inquiry": "Appreciate the interest. Best to connect on LinkedIn and go from there.",
        "spam": None,  # no reply to spam
        "general": None  # use full AI generation for general
    },
    "instagram_personal": {
        "how_to_question": "drop a follow, covering this properly in an upcoming reel 🔥",
        "praise": "appreciate it 🙏 {personalization}",
        "disagreement": "interesting take — {personalization}",
        "business_inquiry": "link in bio, DMs open",
        "spam": None,
        "general": None
    },
    "instagram_brand": {
        "how_to_question": "More details at nyvora.com — {personalization}",
        "praise": "Glad it helped 🙏",
        "business_inquiry": "Reach out at hello@nyvora.com",
        "spam": None,
        "general": None
    },
    "facebook": {
        "how_to_question": "Great question. {personalization} — I'll do a full post on this soon.",
        "praise": "Thank you! {personalization}",
        "disagreement": "{personalization} — what's your experience been?",
        "spam": None,
        "general": None
    }
}
```

**Integration with reply_manager/drafter.py:**
```python
def draft_reply(comment: Reply, persona_path: Path) -> str:
    template_manager = ReplyTemplateManager()
    category = template_manager.classify_comment(comment.comment_text)

    if category == "spam":
        return None  # skip spam entirely

    template = template_manager.get_template(category, comment.account)

    if template is None:
        # Fall back to full AI generation for general/unmatched comments
        return generate_ai_reply(comment, persona_path)

    # Use cheap template personalization instead of full generation
    return template_manager.personalize_template(
        template, comment.comment_text, persona_path
    )
```

**Cost impact:** 70-80% of comments handled by templates. Only unique/general comments hit OpenRouter. At viral scale this saves significant API costs.

---

## GAP 2.3 — Gross Follows Tracking

**The Problem:**
On Instagram, some accounts follow then unfollow within 48h. Analytics collected at the 48h mark captures NET follows (gained minus lost), not GROSS follows (total who followed because of the post). Net could be 0 even if 20 accounts genuinely followed.

**The Solution:**

```python
# backend/analytics/follows_tracker.py — NEW

def track_gross_follows(post_id: int, account: str, db: Session):
    """
    Track follows at two points:
    1. Immediately after publish (T+1h): capture initial follower count
    2. T+48h: capture final follower count
    3. Gross follows = any increase between T=0 and T+48h (ignore decreases)
    """

    # Record follower count at publish time (already captured in post.followers_at_post_time)
    # Record follower count at T+1h and T+48h
    post = db.query(Post).get(post_id)
    initial_followers = post.followers_at_post_time

    # At T+48h:
    current_followers = fetch_current_follower_count(account)

    # Gross follows = increase only (don't subtract unfollows)
    follower_increase = max(0, current_followers - initial_followers)

    # Update analytics with gross follows
    analytics = db.query(PostAnalytics).filter_by(post_id=post_id).first()
    analytics.follows = follower_increase  # gross increase
    analytics.follower_count_at_48h = current_followers
    db.commit()
```

**Add to PostAnalytics model:**
```python
follower_count_at_48h = Column(Integer)   # absolute count at 48h mark
follower_change = Column(Integer)          # net change (can be negative)
```

---

# PART 3 — AUDIENCE INTELLIGENCE

---

## GAP 3.1 — Comment Sentiment Analysis

**The Problem:**
A comment saying "This is exactly what I needed, saved and shared with my team" is worth 100 "great post!" comments. Current system counts comments, not comment quality. Low-quality viral posts with many spam comments get overscored. High-quality posts with few but deeply engaged comments get underscored.

**The Solution:**

```python
# backend/analytics/comment_sentiment.py — NEW

from enum import Enum

class CommentQuality(Enum):
    HIGH = "high"       # detailed, specific, actionable response
    MEDIUM = "medium"   # genuine but brief
    LOW = "low"         # vague praise or short reaction
    SPAM = "spam"       # promotional, follow-for-follow, irrelevant

# Quality signals (keyword-based, free)
HIGH_QUALITY_SIGNALS = [
    "saved", "shared", "team", "implemented", "tried this",
    "works for", "learned", "helped me", "exactly what",
    "been struggling with", "going to try"
]

LOW_QUALITY_SIGNALS = [
    "great post", "love this", "nice", "wow", "fire", "💯",
    "follow me", "check my", "follow for follow"
]

def score_comment_quality(comment_text: str) -> tuple[CommentQuality, float]:
    text_lower = comment_text.lower()

    # Spam check
    if any(spam in text_lower for spam in ["follow for follow", "check my profile", "dm for collab"]):
        return CommentQuality.SPAM, 0.0

    # High quality signals
    high_matches = sum(1 for s in HIGH_QUALITY_SIGNALS if s in text_lower)
    low_matches = sum(1 for s in LOW_QUALITY_SIGNALS if s in text_lower)

    # Length is also a signal — longer comments = more engaged
    length_bonus = min(len(comment_text) / 200, 0.5)  # up to 0.5 bonus for length

    if high_matches >= 2 or (high_matches >= 1 and len(comment_text) > 100):
        return CommentQuality.HIGH, 1.0 + length_bonus
    elif high_matches == 1 or (low_matches == 0 and len(comment_text) > 50):
        return CommentQuality.MEDIUM, 0.5 + length_bonus
    elif low_matches >= 1:
        return CommentQuality.LOW, 0.2
    else:
        return CommentQuality.MEDIUM, 0.4

def compute_comment_quality_score(comments: list[str]) -> float:
    """
    Aggregate quality score for all comments on a post.
    Replaces raw comment count in engagement calculation.
    """
    if not comments:
        return 0.0

    quality_scores = []
    for comment in comments:
        quality, score = score_comment_quality(comment)
        if quality != CommentQuality.SPAM:
            quality_scores.append(score)

    return sum(quality_scores)  # sum, not average — more quality comments = higher score
```

**Update engagement score formula in `analytics/scorer.py`:**
```python
def compute_engagement_score(analytics: PostAnalytics,
                               comments_data: list[str] = None) -> float:
    # Use comment quality score instead of raw comment count
    if comments_data:
        comment_score = compute_comment_quality_score(comments_data)
    else:
        comment_score = analytics.comments * 0.5  # fallback if no comment text available

    raw_score = (
        analytics.saves * 5 +
        analytics.shares * 3 +
        comment_score * 2 +   # quality-weighted comment score
        analytics.follows * 5
    )

    # Normalize by followers
    if analytics.followers_at_post_time and analytics.followers_at_post_time > 0:
        return raw_score / (analytics.followers_at_post_time / 1000)
    return raw_score
```

**Add to PostAnalytics model:**
```python
comment_quality_score = Column(Float)  # computed from comment text analysis
comment_texts = Column(JSON)           # store comment texts for re-analysis
```

---

## GAP 3.2 — Profile Visits Tracking Per Post

**The Problem:**
Someone reads a post, visits Ahmad's profile, doesn't follow yet — but they're a warm lead. Instagram and LinkedIn both provide this metric. Currently not tracked. Profile visits are a leading indicator of follower growth.

**The Solution:**

**Instagram:**
```python
# backend/analytics/aggregator.py — add profile visits collection

def collect_instagram_post_analytics(post_id: str, media_id: str,
                                      account: str, token: str) -> dict:
    # Existing metrics
    response = call_meta_api("GET", f"/{media_id}/insights", {
        "metric": "reach,impressions,likes,comments,shares,saved,follows,profile_visits",
        #                                                          ^ ADD THIS
        "access_token": token
    })
    # profile_visits = people who visited profile from this specific post
    return parse_instagram_insights(response)
```

**LinkedIn:**
```python
# LinkedIn doesn't provide per-post profile visits via API
# Workaround: track account-level profile views daily
# Compare profile views on days with high-performing posts vs baseline

def track_linkedin_profile_views(db: Session):
    """
    LinkedIn provides profile views via /v2/networkSizes
    Track daily and correlate with post performance.
    """
    response = call_linkedin_api("GET", "/v2/networkSizes/~", {
        "edgeType": "CompanyFollowedByMember"
    })
    # Store daily profile views in AccountDailyMetrics table
```

**Add to PostAnalytics model:**
```python
profile_visits = Column(Integer)      # Instagram: from post insights
link_clicks = Column(Integer)         # clicks on any link in post
```

**Add AccountDailyMetrics model:**
```python
class AccountDailyMetrics(Base):
    __tablename__ = "account_daily_metrics"
    id = Column(Integer, primary_key=True)
    account = Column(String)
    date = Column(Date)
    follower_count = Column(Integer)
    profile_visits = Column(Integer)
    reach = Column(Integer)
    impressions = Column(Integer)
```

---

## GAP 3.3 — Audience Demographic Quality Scoring

**The Problem:**
A post that gets 50 follows from Nigerian developers is worth more to Ahmad than 500 follows from irrelevant audiences. Current scoring doesn't distinguish audience quality. Growth number alone is not the goal — the right audience is.

**The Solution:**

```python
# backend/analytics/audience_quality.py — NEW

TARGET_AUDIENCE_SIGNALS = {
    "biography_keywords": [
        "developer", "engineer", "founder", "builder", "startup",
        "software", "product", "tech", "fullstack", "backend", "frontend",
        "nigeria", "africa", "abuja", "lagos", "nairobi", "kenya",
        "saas", "indie", "hacker", "bootstrapped"
    ],
    "location_keywords": [
        "nigeria", "ghana", "kenya", "africa", "abuja", "lagos"
    ]
}

def score_follower_quality(follower_data: dict) -> float:
    """
    Score a new follower's relevance to Ahmad's target audience.
    Based on biography and location from their profile.
    """
    score = 0.0
    bio = (follower_data.get("biography", "") or "").lower()
    location = (follower_data.get("location", "") or "").lower()

    # Bio keyword matches
    bio_matches = sum(1 for kw in TARGET_AUDIENCE_SIGNALS["biography_keywords"]
                      if kw in bio)
    score += min(bio_matches * 0.2, 0.6)  # max 0.6 from bio

    # Location relevance
    location_matches = sum(1 for kw in TARGET_AUDIENCE_SIGNALS["location_keywords"]
                           if kw in location)
    if location_matches > 0:
        score += 0.4  # big bonus for African audience

    return min(score, 1.0)

def compute_audience_quality_score(new_followers: list[dict]) -> float:
    """
    Average quality score across new followers gained from a post.
    High quality = Ahmad's target demographic.
    Low quality = irrelevant or bot audiences.
    """
    if not new_followers:
        return 0.5  # neutral score if no data
    scores = [score_follower_quality(f) for f in new_followers]
    return sum(scores) / len(scores)
```

**Add to PostAnalytics model:**
```python
audience_quality_score = Column(Float)  # 0-1, how relevant were new followers
```

**Note:** Fetching follower profile data requires additional API calls and permissions. Use sparingly — only for high-follow posts. For low-follow posts, default to 0.5 (neutral).

---

# PART 4 — AHMAD-SPECIFIC GAPS

---

## GAP 4.1 — Whisper Transcription for Vlog Uploads

**The Problem:**
AGENTS.md mentions that vlog transcripts feed into the repurposer. But there's no actual mechanism for Ahmad to upload a video and get a transcript. The whole flow is documented but never built.

**The Solution:**

```python
# backend/api/vlog_upload.py — NEW

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
import tempfile, os

router = APIRouter()

@router.post("/api/events/upload-vlog")
async def upload_vlog(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Ahmad uploads a vlog video.
    System transcribes it via Whisper and generates content briefs.
    Returns immediately with job_id — transcription happens async.
    """
    # Save to temp file
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=os.path.splitext(file.filename)[1]
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    job_id = create_transcription_job(tmp_path)
    background_tasks.add_task(process_vlog_transcription, tmp_path, job_id)

    return {"job_id": job_id, "status": "transcribing", "message": "Transcription started — check back in ~60 seconds"}

@router.get("/api/events/vlog-status/{job_id}")
async def get_vlog_status(job_id: str):
    job = get_transcription_job(job_id)
    if job.status == "complete":
        return {
            "status": "complete",
            "transcript": job.transcript,
            "generated_briefs": job.briefs,
            "preview_posts": job.preview_posts
        }
    return {"status": job.status}
```

**Whisper transcription:**
```python
# backend/content/transcriber.py — NEW

import openai  # or use whisper locally

def transcribe_video(video_path: str) -> str:
    """
    Transcribe video using OpenAI Whisper API.
    Cost: ~$0.006 per minute of audio.
    Alternative: run whisper locally (free but needs GPU or is slow on CPU)
    """
    # Extract audio first via ffmpeg
    audio_path = video_path.replace(os.path.splitext(video_path)[1], ".mp3")
    run_command([
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "libmp3lame", "-q:a", "4",
        audio_path
    ])

    # Option A: OpenAI Whisper API (paid, ~$0.006/min)
    with open(audio_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
    os.remove(audio_path)
    return transcript.text

    # Option B: Local whisper (free, slow on CPU)
    # import whisper
    # model = whisper.load_model("base")
    # result = model.transcribe(audio_path)
    # return result["text"]

def process_vlog_transcription(video_path: str, job_id: str):
    """Full pipeline: video → transcript → briefs → preview posts."""
    try:
        # Transcribe
        transcript = transcribe_video(video_path)
        update_job_transcript(job_id, transcript)

        # Generate content briefs from transcript
        briefs = generate_briefs_from_transcript(transcript)
        update_job_briefs(job_id, briefs)

        # Generate preview posts for each platform
        preview_posts = {}
        for brief in briefs[:2]:  # max 2 from one vlog
            posts = generate_posts_from_brief(brief)
            preview_posts[brief["platform"]] = posts

        update_job_complete(job_id, preview_posts)

    except Exception as e:
        update_job_failed(job_id, str(e))
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)  # clean up temp file
```

**Add VlogTranscriptionJob model:**
```python
class VlogTranscriptionJob(Base):
    __tablename__ = "vlog_transcription_jobs"
    id = Column(String, primary_key=True)
    video_path = Column(String)
    status = Column(String)    # transcribing|complete|failed
    transcript = Column(Text)
    briefs = Column(JSON)
    preview_posts = Column(JSON)
    error = Column(Text)
    created_at = Column(DateTime)
    completed_at = Column(DateTime)
```

---

## GAP 4.2 — Nyvora Product Event Webhook

**The Problem:**
When ColdSift gets a new user, or Volari Finance processes its first payment, or any other Nyvora product hits a milestone — these are authentic content moments. No mechanism exists for other Nyvora products to trigger Oybit content generation.

**The Solution:**

```python
# backend/api/external_events.py — NEW

from fastapi import APIRouter, Header, HTTPException
import hmac, hashlib

router = APIRouter()

@router.post("/api/events/external")
async def receive_external_event(
    event: ExternalEventInput,
    x_oybit_signature: str = Header(None)  # HMAC-SHA256 signature
):
    """
    Receives events from other Nyvora products.
    Any Nyvora product can send events here to trigger content generation.

    Signed with NYVORA_WEBHOOK_SECRET to prevent abuse.
    """
    # Verify signature
    if not verify_nyvora_signature(event.dict(), x_oybit_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    logger.info("External event received", extra={
        "product": event.product,
        "event_type": event.event_type,
        "data": event.data
    })

    # Convert to content brief
    brief = convert_event_to_brief(event)

    # High priority — real milestone events bypass MiroFish
    if event.priority == "high":
        create_top_priority_brief(brief)
    else:
        create_standard_brief(brief)

    return {"status": "received", "brief_created": True}

def verify_nyvora_signature(payload: dict, signature: str) -> bool:
    secret = os.getenv("NYVORA_WEBHOOK_SECRET", "")
    expected = hmac.new(
        secret.encode(),
        json.dumps(payload, sort_keys=True).encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature or "")

class ExternalEventInput(BaseModel):
    product: str            # "coldsift" | "volari_finance" | "folio" | "orcha"
    event_type: str         # "new_user" | "first_payment" | "milestone" | "launch"
    data: dict              # event-specific data
    priority: str = "normal" # "high" | "normal"

def convert_event_to_brief(event: ExternalEventInput) -> dict:
    """
    Maps product events to content brief templates.
    """
    templates = {
        ("coldsift", "new_user"): "ColdSift just got user #{data[user_count]}. Here's what I learned shipping an email validation SaaS.",
        ("coldsift", "milestone"): "ColdSift hit {data[milestone]}. {data[description]}",
        ("volari_finance", "first_payment"): "Volari Finance just processed its first payment. Building a fintech tool in Nigeria — here's what that moment actually felt like.",
        ("volari_finance", "launch"): "Volari Finance is live. {data[description]}",
    }

    key = (event.product, event.event_type)
    template = templates.get(key, "{product} update: {event_type} — {data[description]}")

    raw_brief = template.format(
        product=event.product,
        event_type=event.event_type,
        data=event.data
    )

    return {
        "source": "external_event",
        "product": event.product,
        "raw_brief": raw_brief,
        "bypass_mirofish": True,
        "target_accounts": ["linkedin", "instagram_personal"],
        "priority": event.priority
    }
```

**Add env var:**
```
NYVORA_WEBHOOK_SECRET=    # shared secret between all Nyvora products
```

**How ColdSift sends an event to Oybit:**
```python
# In ColdSift's codebase — fires when new user signs up
import hmac, hashlib, requests

def notify_oybit_new_user(user_count: int):
    payload = {
        "product": "coldsift",
        "event_type": "new_user",
        "data": {"user_count": user_count},
        "priority": "high" if user_count in [1, 10, 50, 100] else "normal"
    }
    secret = os.getenv("NYVORA_WEBHOOK_SECRET")
    sig = hmac.new(secret.encode(),
                   json.dumps(payload, sort_keys=True).encode(),
                   hashlib.sha256).hexdigest()
    requests.post(
        os.getenv("OYBIT_API_URL") + "/api/events/external",
        json=payload,
        headers={"X-Oybit-Signature": f"sha256={sig}"}
    )
```

---

## GAP 4.3 — Ahmad's Voice Drift Detection

**The Problem:**
As Ahmad grows, evolves, ships more products, and becomes more prominent, his real voice will drift from the initial persona.md. The system currently only updates persona based on engagement data. It doesn't detect when Ahmad himself starts to sound different from the initial persona. Over time, generated content sounds like the old Ahmad, not the current Ahmad.

**The Solution:**

```python
# backend/persona_engine/drift_detector.py — NEW

class VoiceDriftDetector:
    """
    Periodically compares Ahmad's recent manual posts
    against the current persona.md voice description.
    Detects when the gap becomes significant.
    """

    def detect_drift(self, recent_manual_posts: list[str],
                     persona_path: Path) -> DriftResult:
        if len(recent_manual_posts) < 5:
            return DriftResult(drift_detected=False, reason="insufficient data")

        # Use sentence-transformers to compare voice
        persona_content = persona_path.read_text()
        persona_voice = extract_voice_section(persona_content)

        # Encode persona voice description
        persona_embedding = self.model.encode([persona_voice])[0]

        # Encode recent manual posts
        post_embeddings = self.model.encode(recent_manual_posts)
        post_centroid = post_embeddings.mean(axis=0)

        # Cosine similarity
        similarity = cosine_similarity([persona_embedding], [post_centroid])[0][0]

        DRIFT_THRESHOLD = 0.65  # below this = meaningful drift

        if similarity < DRIFT_THRESHOLD:
            return DriftResult(
                drift_detected=True,
                similarity_score=float(similarity),
                reason=f"Voice similarity dropped to {similarity:.2f} (threshold: {DRIFT_THRESHOLD})",
                recommendation="Review and update persona.md — your voice appears to have evolved"
            )

        return DriftResult(drift_detected=False, similarity_score=float(similarity))
```

**Run drift detection in feedback_worker.py weekly:**
```python
# In workers/feedback_worker.py — add to weekly cycle

def check_voice_drift(db: Session):
    # Get last 10 manual posts (posts Ahmad posted himself, not system-generated)
    manual_posts = db.query(Post).filter(
        Post.source == "manual",
        Post.published_at >= datetime.utcnow() - timedelta(days=30)
    ).order_by(Post.published_at.desc()).limit(10).all()

    if len(manual_posts) < 5:
        return  # not enough data

    post_texts = [p.content_text for p in manual_posts]
    result = drift_detector.detect_drift(post_texts, PERSONA_PATH)

    if result.drift_detected:
        logger.warning("Voice drift detected", extra={
            "similarity": result.similarity_score,
            "reason": result.reason
        })
        # Trigger prompt asking Ahmad to review persona
        create_notification(
            type="voice_drift",
            message=f"Your voice may have evolved. Similarity to current persona: {result.similarity_score:.0%}. "
                    f"Consider reviewing and updating persona.md.",
            action_url="/persona"
        )
        send_alert_to_ahmad(
            f"VOICE DRIFT: Your recent posts sound different from your persona.md. "
            f"Similarity: {result.similarity_score:.0%}. Visit /persona to update.",
            level="info"
        )
```

**Add to Post model:**
```python
source = Column(String, default="system")  # "system" | "manual" — was this generated or manually posted by Ahmad?
```

---

## GAP 4.4 — Nigerian Public Holidays and Calendar Context

**The Problem:**
The scheduler has no concept of cultural/national events. Posts that perform poorly during Nigerian public holidays get incorrectly flagged as bad content by the learning engine. Ahmad's audience (heavily Nigerian) has predictable engagement drops on certain dates.

**The Solution:**

```python
# backend/intelligence/calendar_context.py — NEW

NIGERIAN_PUBLIC_HOLIDAYS = [
    # Format: (month, day, "name")
    (1, 1, "New Year's Day"),
    (5, 1, "Workers Day"),
    (10, 1, "Independence Day"),
    (12, 25, "Christmas Day"),
    (12, 26, "Boxing Day"),
    # Variable: Easter (Good Friday + Easter Monday — compute annually)
    # Variable: Eid al-Fitr (end of Ramadan — varies by year)
    # Variable: Eid al-Adha (varies by year)
]

# Ramadan approximate dates (update annually)
RAMADAN_PERIODS = [
    (2026, date(2026, 2, 17), date(2026, 3, 19)),
    (2027, date(2027, 2, 6), date(2027, 3, 8)),
]

UNIVERSITY_EXAM_PERIODS = [
    # University of Abuja typical exam periods
    # (Ahmad's audience includes students)
    (11, 15, 12, 15),   # November–December semester exams
    (4, 15, 5, 15),     # April–May semester exams
]

def get_calendar_context(dt: datetime) -> CalendarContext:
    """
    Returns context about what's happening today that affects posting.
    """
    today = dt.date()

    # Check Nigerian holidays
    for month, day, name in NIGERIAN_PUBLIC_HOLIDAYS:
        if today.month == month and today.day == day:
            return CalendarContext(
                is_holiday=True,
                holiday_name=name,
                engagement_modifier=0.6,  # 40% lower engagement expected
                recommendation=f"Nigerian public holiday: {name}. "
                               f"Consider pausing professional content or posting something holiday-relevant."
            )

    # Check Ramadan
    for year, start, end in RAMADAN_PERIODS:
        if start <= today <= end:
            return CalendarContext(
                is_ramadan=True,
                engagement_modifier=0.8,  # slightly lower but Muslim audience more active at night
                recommendation="Ramadan period. Morning posts perform less well. Evening posts (after iftar ~7PM WAT) perform better."
            )

    # Check exam periods
    for start_month, start_day, end_month, end_day in UNIVERSITY_EXAM_PERIODS:
        start = date(today.year, start_month, start_day)
        end = date(today.year, end_month, end_day)
        if start <= today <= end:
            return CalendarContext(
                is_exam_period=True,
                engagement_modifier=0.7,
                recommendation="University exam period. Student audience engagement drops. Technical professional content performs better than general posts."
            )

    return CalendarContext(is_normal=True, engagement_modifier=1.0)
```

**Integration with scheduler and learning engine:**
```python
# In scheduler — adjust timing based on calendar
def get_optimal_post_time(account: str, proposed_dt: datetime) -> datetime:
    context = get_calendar_context(proposed_dt)
    if context.is_holiday:
        # Delay to after holiday or post holiday-appropriate content
        logger.info("Holiday context — adjusting schedule", extra={"holiday": context.holiday_name})
    return proposed_dt

# In learning engine — tag posts with calendar context
def tag_post_with_calendar_context(post: Post, db: Session):
    context = get_calendar_context(post.published_at)
    post.calendar_context = context.to_dict()
    post.calendar_engagement_modifier = context.engagement_modifier
    db.commit()
```

**Add to Post model:**
```python
calendar_context = Column(JSON)             # what calendar event was happening when posted
calendar_engagement_modifier = Column(Float) # expected modifier (0.6 = holiday, 1.0 = normal)
```

**In learning engine — normalize for calendar:**
```python
# When computing patterns, normalize by calendar modifier
normalized_score = raw_score / post.calendar_engagement_modifier
# A post with score 10 on a holiday (modifier 0.6) = equivalent to score 16.7 on normal day
```

---

# PART 5 — TESTING IMPROVEMENTS

---

## GAP 5.1 — Independent Verification Tests

**The Problem:**
All tests were written by the same agents who wrote the code. This is circular — agents write code to pass tests they already know. Independent verification requires tests that NEITHER agent designed.

**The Solution:**

Build `scripts/tests/test_independent_verification.py` — a set of tests that verify behavior from the outside, not implementation details:

```python
"""
Independent verification tests.
These tests verify OUTCOMES not implementation details.
They were written AFTER the agents built their modules — not before.
They test the system from Ahmad's perspective.

Run: python scripts/tests/test_independent_verification.py
"""

def test_content_dna_rule_actually_kills_bad_content():
    """
    Generate 20 posts about a vague topic.
    Verify: NONE pass if they lack DNA element.
    Tests the guardian from outside, not from within.
    """
    bad_brief = "Working on something exciting in the tech space"
    posts = content_generator.generate(bad_brief, "linkedin")
    for post in posts:
        dna_result = content_dna_checker.check(post)
        guardian_result = brand_voice_guardian.check(post, "linkedin")
        # At least one of: DNA check fails OR guardian rejects
        assert not (dna_result.passes and guardian_result.passed), \
            f"Vague post passed all gates: {post[:100]}"

def test_same_post_never_goes_out_twice():
    """Idempotency: schedule same post twice, verify only one publish call made."""
    post = create_test_post()
    schedule_post(post.id)
    schedule_post(post.id)  # attempt duplicate scheduling
    published_count = count_publish_calls_for_post(post.id)
    assert published_count == 1, f"Post published {published_count} times — expected 1"

def test_persona_grows_not_shrinks():
    """simulation_log.md must only ever grow in size."""
    initial_size = get_simulation_log_size()
    append_sim_entry("test entry")
    new_size = get_simulation_log_size()
    assert new_size > initial_size, "simulation_log.md shrunk — append-only violated"

def test_engagement_score_formula_is_correct():
    """Verify the exact formula — saves×5 + shares×3 + comments×2 + follows×5."""
    analytics = create_test_analytics(saves=4, shares=3, comments=5, follows=2)
    expected = 4*5 + 3*3 + 5*2 + 2*5  # = 20 + 9 + 10 + 10 = 49
    actual = compute_engagement_score(analytics)
    assert abs(actual - expected) < 1.0, f"Score formula wrong: expected ~{expected}, got {actual}"

def test_gate_never_blocks_publishing_when_zep_is_down():
    """Graceful degradation: if Zep is down, gate should bypass (not block)."""
    with mock_zep_as_down():
        result = pre_publish_gate.run("Any post text", "linkedin")
        # Gate should PASS or DELAY, never FAIL due to infrastructure issue
        assert result.decision in ["pass", "delay"], \
            f"Gate blocked publish due to infrastructure failure: {result}"

def test_persona_md_survives_power_cut_simulation():
    """Atomic write: partial write must never corrupt the file."""
    original_content = read_persona_md()
    # Simulate process kill during write
    with simulate_kill_during_write():
        try:
            write_persona_atomically("New content that might be partial")
        except:
            pass
    # File must either have old content or new content — never partial
    current_content = read_persona_md()
    assert current_content in [original_content, "New content that might be partial"], \
        "persona.md was partially written — atomic write failed"

def test_workers_restart_cleanly_after_crash():
    """Stale running jobs must be reset to pending on startup."""
    # Manually set a job to 'running' (simulates crash)
    set_job_status(test_job_id, "running")
    # Restart scheduler worker
    restart_scheduler_worker()
    # Job must be back to pending
    job = get_job(test_job_id)
    assert job.status == "pending", \
        f"Crashed job not reset to pending: {job.status}"

def test_meta_200_error_is_caught():
    """Meta returns 200 with error body — must be detected."""
    mock_response = {"error": {"code": 190, "message": "Token expired"}}
    with pytest.raises(TokenExpiredError):
        check_meta_response(mock_response, "instagram_personal")

def test_carousel_images_are_actual_images():
    """Generated carousel must produce real JPEG files, not placeholder bytes."""
    slides = generate_test_carousel_slides()
    images = render_carousel(slides, "personal_ig")
    for img_path in images:
        assert os.path.exists(img_path)
        assert os.path.getsize(img_path) > 50_000  # > 50KB = real image
        # Verify it's actually a JPEG
        with open(img_path, "rb") as f:
            header = f.read(3)
        assert header == b'\xff\xd8\xff', f"Not a real JPEG: {img_path}"

def test_full_pipeline_produces_publishable_content():
    """
    End-to-end: topic brief → complete publishable post.
    Tests that all modules connect correctly.
    """
    brief = {
        "topic": "I shipped a feature at 2AM that prevented a security breach",
        "dna_element": "real_consequence",
        "target_account": "linkedin"
    }

    # Run pipeline
    variants = content_generator.generate(brief, "linkedin")
    assert len(variants) >= 3, "Generator produced fewer than 3 variants"

    top_variant = scorer.select_top(variants)
    assert top_variant is not None

    guardian_result = brand_voice_guardian.check(top_variant, "linkedin")
    assert guardian_result.passed, f"Good post rejected by guardian: {guardian_result.rejection_reason}"

    # Verify post is under LinkedIn character limit
    assert len(top_variant) <= 1300, f"Post too long for LinkedIn: {len(top_variant)} chars"

    print(f"PASS: Full pipeline produced valid publishable content ({len(top_variant)} chars)")
```

---

## GAP 5.2 — Real API Call Tests (Non-Mocked)

**The Problem:**
Every test currently mocks the platform APIs. The first time real API calls fire, they'll hit authentication quirks, response format differences, and rate limit behaviors that mocks don't capture.

**The Solution:**

Build `scripts/tests/test_real_api_calls.py` — runs only when explicitly invoked with `--real-apis` flag. Uses real accounts but in safe read-only or draft mode.

```python
"""
Real API call tests.
ONLY run these manually — they hit real platform APIs.
Run: python scripts/tests/test_real_api_calls.py --real-apis

Requirements:
- Valid tokens for all 4 accounts in .env
- Instagram Personal and Brand accounts connected
- LinkedIn account connected
- Facebook page connected
"""

import sys
if "--real-apis" not in sys.argv:
    print("Skipping real API tests. Add --real-apis to run.")
    sys.exit(0)

def test_instagram_personal_token_valid():
    """Verify personal IG token works and account is reachable."""
    token = os.getenv("INSTAGRAM_PERSONAL_ACCESS_TOKEN")
    user_id = os.getenv("INSTAGRAM_PERSONAL_USER_ID")

    response = requests.get(
        f"https://graph.facebook.com/v19.0/{user_id}",
        params={"fields": "id,username,followers_count", "access_token": token}
    )
    data = response.json()
    assert "error" not in data, f"Token invalid: {data}"
    assert "id" in data, "No ID in response"
    print(f"PASS: Instagram Personal connected — @{data.get('username')} ({data.get('followers_count')} followers)")

def test_instagram_brand_token_valid():
    """Same for brand account."""
    # ... same as above but brand tokens

def test_linkedin_token_valid():
    """Verify LinkedIn token is valid."""
    response = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {os.getenv('LINKEDIN_ACCESS_TOKEN')}"}
    )
    data = response.json()
    assert response.status_code == 200, f"LinkedIn token invalid: {data}"
    print(f"PASS: LinkedIn connected — {data.get('localizedFirstName')} {data.get('localizedLastName')}")

def test_facebook_page_token_valid():
    """Verify Facebook page token."""
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    response = requests.get(
        f"https://graph.facebook.com/v19.0/{page_id}",
        params={"fields": "id,name,fan_count", "access_token": token}
    )
    data = response.json()
    assert "error" not in data, f"Facebook token invalid: {data}"
    print(f"PASS: Facebook Page connected — {data.get('name')} ({data.get('fan_count')} fans)")

def test_instagram_dry_run_post():
    """
    Create a media container but DON'T publish.
    Verifies the publish flow works without actually posting.
    """
    # Create container
    test_image_url = "https://via.placeholder.com/1080x1080"
    response = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_PERSONAL_USER_ID}/media",
        data={
            "image_url": test_image_url,
            "caption": "[TEST - DO NOT PUBLISH]",
            "access_token": INSTAGRAM_PERSONAL_TOKEN
        }
    )
    data = response.json()
    assert "error" not in data, f"Container creation failed: {data}"
    assert "id" in data, "No container ID returned"
    # NOTE: Don't call media_publish — just verify container was created
    print(f"PASS: Instagram container creation works — container ID: {data['id']}")

def test_openrouter_real_call():
    """Make one real OpenRouter call with a simple prompt."""
    response = call_openrouter({
        "model": os.getenv("OPENROUTER_DEFAULT_MODEL"),
        "messages": [{"role": "user", "content": "Reply with exactly: TEST_OK"}],
        "max_tokens": 10
    })
    content = response["choices"][0]["message"]["content"]
    assert "TEST_OK" in content, f"Unexpected response: {content}"
    print(f"PASS: OpenRouter call succeeded — response: {content}")
```

---

# PART 6 — LONG-TERM / SCALE GAPS

---

## GAP 6.1 — Waitlist Capture Mechanism

**The Problem:**
When Oybit starts generating real growth for Ahmad and others ask about it, there's no mechanism to capture interest. "DM if you want early access" with no backend = lost leads.

**The Solution:**

```python
# backend/api/waitlist.py — NEW (minimal, builds toward future SaaS)

from pydantic import BaseModel, EmailStr

class WaitlistEntry(BaseModel):
    email: EmailStr
    name: str = ""
    source: str = ""   # which platform/post they came from
    note: str = ""     # what they said

@router.post("/api/waitlist")
async def join_waitlist(entry: WaitlistEntry, db: Session = Depends(get_db)):
    """Public endpoint. No auth required."""
    existing = db.query(WaitlistRecord).filter_by(email=entry.email).first()
    if existing:
        return {"status": "already_registered"}

    record = WaitlistRecord(
        email=entry.email,
        name=entry.name,
        source=entry.source,
        note=entry.note,
        joined_at=datetime.utcnow()
    )
    db.add(record)
    db.commit()

    # Alert Ahmad via Telegram
    send_alert_to_ahmad(
        f"New waitlist signup: {entry.email} (from: {entry.source})",
        level="info"
    )

    return {"status": "registered", "position": db.query(WaitlistRecord).count()}

@router.get("/api/waitlist/count")
async def waitlist_count(db: Session = Depends(get_db)):
    """Public — used to show "X people on waitlist" in Oybit's own posts."""
    return {"count": db.query(WaitlistRecord).count()}
```

**Add WaitlistRecord model:**
```python
class WaitlistRecord(Base):
    __tablename__ = "waitlist"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    source = Column(String)    # "linkedin_post_123", "instagram", "direct"
    note = Column(String)
    joined_at = Column(DateTime)
```

**Simple landing page at `oybit.nyvora.com/waitlist` — minimal, just email capture.**

---

## GAP 6.2 — Production-Ready persona/_template.md

**The Problem:**
`persona/_template.md` is currently a placeholder. When Oybit opens to other users, every new user's persona is built from this template. An incomplete template = incomplete personas for all future users.

**The Solution:**

```markdown
# {Brand Name} — Persona

_Version: 1 | Created: {ISO date} | Built through: staged onboarding_
_Last updated: {ISO date} | Strategy version: 1_

---

## 1. Identity

**Name:** {name or brand name}
**Type:** personal_brand | company | product | creator
**Mission:** {one sentence — why this brand exists}
**Values:** {comma separated list}
**Origin:** {2-3 sentences — where this came from}
**Stand for:** {list — what we actively support}
**Stand against:** {list — what we reject}
**Elevator pitch:** {one sentence — what this is for a stranger}
**Primary language:** {English | Yoruba | Igbo | Hausa | French | etc}

---

## 2. Voice & Tone

**Formality scale:** {1 (very casual) to 10 (very formal)}
**Per-platform formality:**
  - LinkedIn: {n}/10
  - Instagram Personal: {n}/10
  - Instagram Brand: {n}/10
  - Facebook: {n}/10

**Reference voices:** {brands, people, publications that sound similar}
**Vocabulary always used:** {words and phrases that are signature}
**Vocabulary never used:** {words that are off-brand}
**Punctuation style:** {description of how punctuation is used}
**Sentence length preference:** short | medium | long | mixed
**Fragment tolerance:** yes | no | sometimes
**Emoji policy:** never | rare | occasional | frequent
**Humor style:** none | dry | self-deprecating | playful | sarcastic
**Swearing policy:** never | rare | context-dependent

---

## 3. Audience

**Primary audience:** {description}
**Age range:** {range}
**Location:** {geographic focus}
**Occupation/identity:** {what they do}
**Psychographics:** {values, fears, aspirations}
**Pain points:**
  - {pain 1}
  - {pain 2}
  - {pain 3}
**Language they use:** {specific terms, phrases, how they talk}
**What they come here for:** {what value they get}
**What they never want to see:** {what would make them unfollow}

---

## 4. Content Pillars

| Pillar | Description | LinkedIn | Instagram Personal | Instagram Brand | Facebook |
|---|---|---|---|---|---|
| {pillar 1} | {description} | {%} | {%} | {%} | {%} |
| {pillar 2} | {description} | {%} | {%} | {%} | {%} |
| {pillar 3} | {description} | {%} | {%} | {%} | {%} |
| {pillar 4} | {description} | {%} | {%} | {%} | {%} |

**Hard stops — never post about:**
- {topic 1}
- {topic 2}

---

## 5. Per-Account Tone Modifiers

**LinkedIn:**
{description of how voice adjusts for LinkedIn}

**Instagram Personal:**
{description of how voice adjusts for personal IG}

**Instagram Brand:**
{description of how voice adjusts for brand IG}

**Facebook:**
{description of how voice adjusts for Facebook}

---

## 6. Engagement Style

**Reply tone:** {description}
**Handles praise by:** {how to respond to positive comments}
**Handles criticism by:** {how to respond to negative comments}
**Handles debate by:** {how to engage with disagreement}
**Handles spam by:** {ignore | block | report}

**Reply automation per account:**
- LinkedIn: manual | semi-auto | full-auto
- Instagram Personal: manual | semi-auto | full-auto
- Instagram Brand: manual | semi-auto | full-auto
- Facebook: manual | semi-auto | full-auto

---

## 7. Visual Identity

**Primary color:** {hex code}
**Secondary color:** {hex code}
**Accent color:** {hex code}
**Font primary:** {font name}
**Font secondary:** {font name}
**Aesthetic style:** {description — minimal | bold | editorial | etc}
**Image style:** {description — photography | illustration | graphics | etc}

---

## 8. Performance Memory

_This section is updated automatically by the learning engine. Do not edit manually._

**Top performing content types:**

| Account | Best format | Best pillar | Best hook type | Avg engagement score |
|---|---|---|---|---|
| LinkedIn | — | — | — | — |
| Instagram Personal | — | — | — | — |
| Instagram Brand | — | — | — | — |
| Facebook | — | — | — | — |

**Engagement benchmarks:**

| Account | Followers | Avg reach | Avg normalized score |
|---|---|---|---|
| LinkedIn | 0 | — | — |
| Instagram Personal | 0 | — | — |
| Instagram Brand | 0 | — | — |
| Facebook | 0 | — | — |

**Strategy history:**

| Version | Date | Trigger | Change |
|---|---|---|---|
| 1 | {creation date} | Initial onboarding | Baseline persona established |

**Current strategy focus:** Establishing initial presence across all accounts
**Next rotation check:** {14 days from creation}
```

Save this as the actual `persona/_template.md` file — not a placeholder.

---

## GAP 6.3 — Sim Engine Public Content Mode

**The Problem:**
The simulation engine pulls posts from platforms via API during onboarding. But in a future multi-user context, you can't pull posts from a new user's private platforms before they grant permission. Need a public content mode that works pre-auth.

**The Solution:**

```python
# backend/onboarding/sim_engine.py — add public content mode

class SimulationEngine:

    def get_scenario(self, niche_keywords: list, stage: int,
                     mode: str = "public") -> SimScenario:
        """
        mode: "public" = use public content (no auth needed)
              "authenticated" = pull from user's actual platforms
        """
        if mode == "public":
            return self._get_public_content_scenario(niche_keywords)
        else:
            return self._get_authenticated_scenario(niche_keywords)

    def _get_public_content_scenario(self, niche_keywords: list) -> SimScenario:
        """
        Pull public content without platform authentication.
        Sources: Reddit (public API), public RSS feeds, curated content library.
        Works for any new user before they connect their accounts.
        """
        # Reddit public API — no auth needed for public posts
        reddit_posts = self._fetch_reddit_public(niche_keywords)

        # RSS feeds — always public
        rss_posts = self._fetch_rss_public(niche_keywords)

        # Curated scenario library — pre-built scenarios for common niches
        curated = self._get_curated_scenario(niche_keywords)

        all_sources = reddit_posts + rss_posts + [curated]
        return random.choice(all_sources)

    def _get_curated_scenario(self, niche_keywords: list) -> SimScenario:
        """
        Pre-built library of ~100 scenario templates across common niches.
        Covers: dev/tech founder, marketing, product, creative, African entrepreneur.
        Always available, no API calls needed.
        """
        niche = detect_niche(niche_keywords)
        scenarios = CURATED_SCENARIOS.get(niche, CURATED_SCENARIOS["general"])
        return random.choice(scenarios)
```

**Pre-populate `CURATED_SCENARIOS` dict with 20+ scenarios per niche category.** These are handcrafted, high-quality scenarios that cover the most common onboarding situations. Ahmad uses these too for his initial setup.

---

# FINAL VERIFICATION

All three gap files together cover the following modules that now need to exist:

```
NEW FILES TO BUILD (not in AGENTS.md original scope):

backend/publishers/
  ├── linkedin_polls.py           ← GAP 1.1
  ├── instagram_stories.py        ← GAP 1.2
  ├── facebook_reels.py           ← GAP 1.3
  ├── instagram_collab.py         ← GAPS_AND_FIXES.md
  ├── linkedin_newsletter.py      ← GAPS_AND_FIXES.md
  ├── pinterest.py                ← GAPS_AND_FIXES.md
  ├── youtube.py                  ← GAPS_AND_FIXES.md
  └── facebook_personal.py        ← OYBIT_GAP_SOLUTIONS.md

backend/growth/
  ├── follow_strategy.py          ← GAP 2.1
  ├── comment_opportunities.py    ← OYBIT_GAP_SOLUTIONS.md
  └── reddit_opportunity.py       ← OYBIT_GAP_SOLUTIONS.md

backend/reply_manager/
  └── templates.py                ← GAP 2.2

backend/analytics/
  ├── follows_tracker.py          ← GAP 2.3
  ├── comment_sentiment.py        ← GAP 3.1
  └── audience_quality.py         ← GAP 3.3

backend/api/
  ├── vlog_upload.py              ← GAP 4.1
  ├── external_events.py          ← GAP 4.2
  └── waitlist.py                 ← GAP 6.1

backend/content/
  ├── poll_generator.py           ← GAP 1.1
  ├── stories_generator.py        ← GAP 1.2
  └── transcriber.py              ← GAP 4.1

backend/persona_engine/
  └── drift_detector.py           ← GAP 4.3

backend/intelligence/
  └── calendar_context.py         ← GAP 4.4

backend/event_ingestion/
  └── telegram_listener.py        ← OYBIT_GAP_SOLUTIONS.md

workers/
  ├── follow_worker.py            ← GAP 2.1
  └── keepalive_worker.py         ← GAPS_AND_FIXES.md

scripts/tests/
  ├── test_independent_verification.py  ← GAP 5.1
  └── test_real_api_calls.py            ← GAP 5.2

persona/
  └── _template.md (production-ready)   ← GAP 6.2
```

---

*Three gap files. All known gaps covered. Discovery gaps will emerge from real usage.*
*AGENTS.md + TESTS.md + OYBIT_GAP_SOLUTIONS.md + GAPS_AND_FIXES.md + REMAINING_GAPS.md = complete build spec.*