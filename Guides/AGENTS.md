# AGENTS.md — Oybit Multi-Agent Build Manifest
# Read this file first. Know your role. Build your part. Don't touch what isn't yours.

---

## Project Context

You are building **Oybit** — Ahmad's personal autonomous content engine.
Single user. Four social accounts (Instagram Personal, Instagram Brand, Facebook, LinkedIn).
Goal: generate, score, gate, publish, and learn from content automatically.

Full system understanding is in these files — read them before writing a single line:
- `product.md` — what Oybit is and why
- `architecture.md` — full folder structure + data models + deployment
- `features.md` — every module in detail
- `how_it_works.md` — the complete end-to-end flow
- `integrations_and_apis.md` — every API endpoint used
- `platforms.md` — per-account strategy
- `persona_learning_and_trend_engine.md` — MiroFish + persona system deep dive
- `deployment_and_runbook.md` — Railway config + env vars + operations

**Stack:** Python + FastAPI (backend) · Next.js + React (frontend) · PostgreSQL · SQLite · Redis · Railway (deploy)

---

## Agent Roster

| Agent | Model | Role |
|---|---|---|
| **Agent A** | Claude Opus 4.6 | The Brain — intelligence, persona, learning, scoring |
| **Agent B** | Gemini 3 Pro | The Engine — publishers, render, scheduler, workers, frontend |

These two agents own the entire codebase. No overlap. No conflicts.
Each agent works in their assigned modules only.

---

---

# AGENT A — Claude Opus 4.6
## Role: The Brain

You own everything that thinks. Every module that involves reasoning,
learning, prediction, scoring, or understanding Ahmad's voice.
You build the system's intelligence.

---

## Read first (mandatory before writing any code)

```
product.md
architecture.md
features.md (Modules 1–9, 14, 15)
how_it_works.md
persona_learning_and_trend_engine.md
```

---

## Your Modules

### 1. MiroFish Intelligence Layer
**Path:** `backend/intelligence/mirofish/`

Build all 7 files:

**`seed_builder.py`**
- Collects daily seed content from RSS feeds, Reddit hot posts, Google Trends
- RSS feeds: TechCrunch, HackerNews, r/entrepreneur, r/webdev, r/SideProject, r/startups
- Google Trends via `pytrends` for keywords from persona.md content pillars
- Reddit via PRAW: pull top 10 hot posts from relevant subreddits
- Output: list of 30–50 seed documents (title, content, source, timestamp)

**`graph_builder.py`**
- Takes seed documents → runs GraphRAG entity + relationship extraction
- Extracts: companies, people, events, concepts, trends
- Maps relationships between entities
- Detects community clusters (relevant to Ahmad's niche)
- Output: structured knowledge graph JSON

**`agent_spawner.py`**
- Takes knowledge graph → generates agent personas representing Ahmad's audience
- Agent types: Nigerian developer, indie hacker, LinkedIn professional, startup founder, tech enthusiast, skeptic, early adopter
- Each agent gets: personality profile, initial opinion on current topics, social relationships
- Uses Zep Cloud for persistent agent memory (ZEP_API_KEY from env)
- Output: list of agent configurations

**`simulation_runner.py`**
- Takes agent configs → runs OASIS simulation (pip: oasis-social)
- Runs 4 rounds across Twitter-like + Reddit-like environments
- Round 1: initial reactions. Round 2: opinion spread. Round 3: counter-narratives. Round 4: emergence.
- Output: raw simulation results per agent per round

**`report_agent.py`**
- Takes simulation results → synthesises into structured prediction
- Output JSON:
```json
{
  "rising_narratives": [{"topic": "", "relevance_to_persona": 0.0, "predicted_peak": "", "framing_suggestion": "", "resonant_angles": [], "avoid_angles": [], "confidence": 0.0}],
  "timing_recommendations": {"linkedin": "", "instagram_personal": "", "instagram_brand": "", "facebook": ""},
  "narrative_forecast_72h": "",
  "avoid_posting_now": []
}
```

**`pre_publish_gate.py`**
- Takes a fully rendered post → runs focused simulation against live discourse
- Builds gate seed: rendered post + current live signals
- Spawns fresh agents representing today's audience state
- Runs 3-round focused simulation: "agents see this post, what happens?"
- Outputs: GateResult(decision=pass|fail|delay, confidence, predicted_saves, predicted_comments, failure_reason, recommended_delay, early_learning_signal)
- Sends early_learning_signal to learning_engine IMMEDIATELY (before real data)

**`narrative_forecaster.py`**
- Orchestrates the full daily pipeline: seed → graph → agents → simulation → report
- Called by mirofish_worker.py at 5AM
- Saves output to PostgreSQL MiroFishRun table

---

### 2. Opportunity Detector
**Path:** `backend/intelligence/opportunity_detector.py`

- Takes MiroFish narrative forecast output
- Filters each narrative through persona.md lens:
  - Is this Ahmad's niche? (relevance_to_persona > 0.6)
  - Does it pass Content DNA Rule?
- **Content DNA Rule — hard filter (implement exactly):**
  Every topic brief must contain at least one of:
  - system_insight: reveals how something actually works
  - real_consequence: something that happened or will happen
  - technical_mechanism: the specific thing that caused it
  - contradiction: something unexpected or counterintuitive
  Posts without any of these are DISCARDED. No exceptions.
- Output: list of ApprovedTopicBrief(topic, angle, dna_element, target_accounts[], timing, platform_notes)

---

### 3. Content DNA Checker
**Path:** `backend/intelligence/content_dna_checker.py`

- Standalone function called by both opportunity_detector and brand_voice_guardian
- Takes any text → classifies which DNA elements are present
- Returns: DNAResult(has_system_insight, has_real_consequence, has_technical_mechanism, has_contradiction, passes=bool)
- Uses OpenRouter for classification (OPENROUTER_API_KEY from env)

---

### 4. Multi-Variant Scoring AI
**Path:** `backend/intelligence/scorer.py`

Implement the scoring formula exactly:
```python
import math

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def score_post(
    topicality: float,      # T: MiroFish trend score 0-1
    hook_strength: float,   # H: predicted hook curiosity 0-1
    persona_alignment: float,  # P: semantic match to persona history 0-1
    alpha_0: float = -0.5,
    alpha_1: float = 1.2,
    alpha_2: float = 1.5,
    alpha_3: float = 1.0
) -> float:
    return sigmoid(alpha_0 + alpha_1*topicality + alpha_2*hook_strength + alpha_3*persona_alignment)
```

- `hook_strength`: measure by comparing opening line to PatternDB top hooks (semantic similarity via sentence-transformers)
- `persona_alignment`: semantic similarity between post content and persona.md voice section
- Score all candidates → select top 1–2 → log rest with rejection reason
- Save scores to Post record (score_topicality, score_hook, score_persona, score_total)

---

### 5. Persona Engine
**Path:** `backend/persona_engine/`

**`builder.py`**
- Takes onboarding answers (dict of all stage responses)
- Builds structured persona.md file using the template in `persona_learning_and_trend_engine.md`
- Writes to `/data/personas/ahmad/persona.md`
- Creates empty `/data/personas/ahmad/simulation_log.md` with header

**`updater.py`**
- Takes PatternDB data + feedback signal
- Implements 4 update triggers:
  1. Time-based: 14 days since last update → patch performance memory
  2. Engagement drop: avg score drops >20% over 5 consecutive posts → rotate strategy
  3. Post volume: every 30 posts → refresh performance memory
  4. Pattern shift: winning combo changes significantly → update pillar weights
- Reads current persona.md → applies patches → writes back
- Appends new version to Strategy History section

**`prompt_builder.py`**
- Reads persona.md (full) + simulation_log.md (last 10 entries)
- Takes: platform name, topic brief, format type
- Returns: structured system prompt for OpenRouter generation call
- Must include: persona voice, platform tone modifier, content pillar, Content DNA requirement, winning post structure, hard stops
- Winning post structure to inject:
  ```
  Real situation → system insight → constraint/lesson → relatable framing → minimal CTA
  ```

**`rotation_trigger.py`**
- Monitors engagement trends across posts
- Triggers strategy rotation when: consecutive drop OR time threshold OR pattern shift
- Calls updater.py with rotation flag when triggered

---

### 6. Onboarding — Simulation Engine
**Path:** `backend/onboarding/`

**`questions.py`**
- Full 180-question bank organized by stage (1–6)
- Stage 1: 30 core identity + voice + audience questions
- Stage 2: 30 simulation scenarios (see format below)
- Stage 3: 30 tone deep-dive questions
- Stage 4: 15 content boundary questions (unlocks at 2 weeks)
- Stage 5: 15 audience empathy questions (unlocks after 20 posts)
- Stage 6: 10 engagement style questions (unlocks after 50 posts)
- Each question has: id, stage, question_text, question_type (open/choice/scale), options (if choice)

**`sim_engine.py`**
- Pulls real posts from target platforms via their APIs based on user's declared interests
- Presents each post as an interactive scenario with specific scenario_type:
  - `trending_post_reaction` — "This is trending in your niche. Like/share/ignore/create similar?"
  - `comment_reply_test` — "Here's a comment on a post like yours. How do you reply?"
  - `trend_format_test` — "This format is going viral. Would you use it? How?"
  - `controversy_response_test` — "A brand in your space posted something controversial. Do you respond?"
  - `meme_adaptation_test` — "This meme format is everywhere. Does your brand use it?"
- Records every reaction + decision + typed response
- Generates AI inference: "What AI learned" from each response
- **Appends to simulation_log.md (NEVER overwrites, only appends):**
  ```markdown
  ## Session [ISO date]

  ### Sim [n]
  Platform: [platform]
  Scenario type: [type]
  Shown: [content shown]
  Reaction: [user reaction]
  Decision: [user decision]
  What AI learned: [AI inference about voice/preferences/instincts]
  ```

**`calibration.py`**
- After every manual post Ahmad publishes directly: prompts "How authentically does this sound like you? (1–10, why?)"
- Stores rating + reasoning
- Low ratings (< 6) trigger targeted follow-up questions
- High ratings (≥ 8) reinforce current persona weights
- All responses appended to simulation_log.md

---

### 7. Brand Voice Guardian
**Path:** `backend/brand_voice_guardian/checker.py`

Runs on every candidate before rendering. Returns CheckResult(passed, near_pass, rejected, edit_suggestion, rejection_reason).

Implement these checks IN ORDER (fail fast):

1. **Content DNA check** — call content_dna_checker.py. If no DNA element found → REJECT immediately.
2. **Hard stops check** — scan for any topic in persona.md hard_stops list. If found → REJECT.
3. **Tone similarity check** — semantic similarity between post and persona.md voice section. If < 0.55 → REJECT.
4. **Platform appropriateness** — check length against platform limits, format match, tone modifier match. If fails → NEAR_PASS with edit suggestion.
5. **Brand safety** — basic scan for potential misreadings, controversy exposure, anything that could embarrass Nyvora. If flagged → NEAR_PASS with warning.

Only after passing all 5 checks → PASS.

---

### 8. Learning Engine
**Path:** `backend/feedback_loop/`

**`learning_engine.py`**
- Takes TWO inputs for each post:
  1. MiroFish pre-publish gate result (early_learning_signal stored at gate time)
  2. Real engagement score collected 48h after publishing
- Engagement score formula (implement exactly):
  ```python
  def compute_engagement_score(saves, shares, comments, follows):
      return saves*5 + shares*3 + comments*2 + follows*5
  ```
- Tags post in PatternDB: hook_type + topic_pillar + format + account
- Pattern detection across last 30 posts minimum:
  - Find combinations with avg_score significantly above baseline
  - Find combinations consistently underperforming
  - Minimum 10 posts per combination before drawing conclusions
- Calls persona_patcher.py when update triggers met
- Calls mirofish_refiner.py with updated audience signal

**`persona_patcher.py`**
- Reads current persona.md
- Applies targeted patches:
  - Updates performance memory table
  - Rebalances content pillar posting weights based on PatternDB
  - Updates per-account tone adjustments if one account outperforms
  - Appends new version to Strategy History
  - Updates current strategy focus
  - Sets next rotation check date
- Writes back to `/data/personas/ahmad/persona.md`
- Logs every change made

**`mirofish_refiner.py`**
- Builds refinement signal from PatternDB patterns:
  ```python
  {
      "performing_topics": [...],
      "underperforming_topics": [...],
      "winning_hook_types": [...],
      "audience_response_patterns": {...}
  }
  ```
- Sends signal to MiroFish agent_spawner to weight future agent populations
- More agents matching Ahmad's best-responding audience segments in future sims

---

### 9. Content Generator (prompt logic only)
**Path:** `backend/content/generator.py`

You own the prompt assembly logic. Agent B owns the OpenRouter call wrapper.

Build:
- `assemble_generation_prompt(persona_path, simulation_log_path, topic_brief, platform, format_type, account)` → returns full system prompt + user prompt
- Must read full persona.md every call
- Must read last 10 simulation_log.md entries every call
- Must inject platform tone modifier for the specific account
- Must inject winning post structure
- Must request 5–20 variants with different hook styles
- Must specify Content DNA requirement in prompt

---

## Your API Endpoints (implement in `backend/api/`)

```
# Onboarding
GET    /api/onboarding/stage/:n                # Get stage questions
POST   /api/onboarding/stage/:n                # Submit answers
GET    /api/onboarding/sim                     # Get next simulation scenario
POST   /api/onboarding/sim                     # Submit sim reaction + decision
POST   /api/onboarding/calibrate               # Submit post authenticity rating

# Persona
GET    /api/persona                            # Read current persona.md
PATCH  /api/persona                            # Manual edit sections
GET    /api/persona/export                     # Download persona.md
POST   /api/persona/import                     # Upload persona.md

# Intelligence
GET    /api/intelligence/feed                  # Latest MiroFish narrative forecast
POST   /api/intelligence/run                   # Trigger MiroFish run manually
GET    /api/intelligence/gate/:post_id         # Get pre-publish gate result
GET    /api/intelligence/trends                # Aggregated trend signals

# Content (scoring + guardian only — generation call is Agent B's)
POST   /api/content/score                      # Score a list of candidates
POST   /api/content/guardian-check             # Run Brand Voice Guardian on text
```

---

## Your Database Models (implement in `backend/db/models.py`, coordinate with Agent B)

```python
class MiroFishRun(Base):
    id, run_type, seed_content, narrative_output, timing_recommendations,
    confidence_score, created_at

class PrePublishGate(Base):
    id, post_id, simulation_result, confidence_score, failure_reason,
    recommended_delay, early_learning_signal, created_at

class SimulationLogEntry(Base):
    id, session_date, sim_number, platform, scenario_type, shown_content,
    user_reaction, user_decision, ai_learned, appended_at

class PatternDB(Base):
    id, account, hook_type, topic_pillar, format, avg_engagement_score,
    post_count, last_updated

class OnboardingSession(Base):
    id, stage, answers, completed_at
```

---

## Your Workers (implement in `workers/`)

**`mirofish_worker.py`**
- Runs daily at MIROFISH_RUN_HOUR (5AM WAT from env)
- Calls narrative_forecaster.py → saves result to MiroFishRun table
- Falls back to cached last forecast if simulation fails (never block content generation)

**`feedback_worker.py`**
- Runs weekly on FEEDBACK_RUN_DAY at FEEDBACK_RUN_HOUR (Sunday 2AM from env)
- Calls learning_engine.py for all posts published in the last 7 days that have 48h+ of data
- Logs every pattern found + every persona patch applied

---

## Dependencies (add to requirements.txt)

```
graphrag
oasis-social
zep-cloud
sentence-transformers
pytrends
praw
feedparser
```

---

## Coordination Notes for Agent A

- Do NOT touch any publisher files — those are Agent B's
- Do NOT touch render_engine/ — Agent B's
- Do NOT touch the frontend — Agent B's
- Do NOT touch scheduler_worker.py — Agent B's
- Coordinate on `backend/db/models.py` — you define your models, Agent B defines theirs, merge at end
- Coordinate on `backend/content/generator.py` — you write the prompt assembly, Agent B writes the OpenRouter call wrapper
- Write all persona files to `/data/personas/ahmad/` on Railway Volume
- All simulation log writes must be append-only — NEVER truncate or overwrite simulation_log.md

---

---

# AGENT B — Gemini 3 Pro
## Role: The Engine

You own everything that moves. Every module that publishes, renders,
schedules, fetches, and displays. You build the system's infrastructure.

---

## Read first (mandatory before writing any code)

```
product.md
architecture.md
features.md (Modules 10–13)
how_it_works.md
integrations_and_apis.md
deployment_and_runbook.md
```

---

## Your Modules

### 1. Platform Publishers
**Path:** `backend/publishers/`

Build all 5 files. Each handles its own OAuth tokens, format compliance, rate limiting, retry logic (3 attempts, exponential backoff: 5s/15s/45s), error logging, and post ID capture for analytics.

**`instagram_personal.py`**
- Account: Ahmad's personal Instagram
- Reads token from token_store (INSTAGRAM_PERSONAL_ACCESS_TOKEN, INSTAGRAM_PERSONAL_USER_ID)
- Supports: single image, carousel (up to 10 slides), Reel (video), Story (photo/video)
- Carousel flow: create each item container → create carousel container → publish
- Reel flow: create container with media_type=REELS → poll for VIDEO_READY → publish
- All API calls to `https://graph.facebook.com/v19.0`
- Log published post_id to Post record for analytics linking

**`instagram_brand.py`**
- Account: Nyvora brand Instagram
- Same flow as instagram_personal.py but uses INSTAGRAM_BRAND_ACCESS_TOKEN, INSTAGRAM_BRAND_USER_ID
- Different account — separate token management
- Same supported formats

**`facebook.py`**
- Account: Nyvora Facebook page
- Uses FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID
- Supports: text post (/{page-id}/feed), photo post (/{page-id}/photos), video post (/{page-id}/videos)
- Always use page access token — never user token for page posts

**`linkedin.py`**
- Account: Ahmad's LinkedIn profile
- Uses LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN
- Supports: text post, image post (register upload → upload binary → create post)
- Text post endpoint: POST /v2/ugcPosts
- Image upload: POST /v2/assets?action=registerUpload → PUT {uploadUrl} → POST /v2/ugcPosts with media
- Header: `X-Restli-Protocol-Version: 2.0.0`

**`dispatcher.py`**
- Takes Post record + account field
- Routes to correct publisher(s)
- Handles cross-posting (same post to multiple accounts)
- Returns dispatch result (success/failure per account)

---

### 2. Token Store
**Path:** `backend/token_store/`

**`store.py`**
- Encrypted storage for all 4 account tokens in PostgreSQL
- Use Fernet symmetric encryption (cryptography library)
- Encryption key from SECRET_KEY env var
- Methods: save_token(account, token_type, value, expiry), get_token(account, token_type), delete_token(account, token_type)
- Token types per account:
  - Meta accounts: access_token, token_expiry
  - LinkedIn: access_token, refresh_token, token_expiry

**`refresher.py`**
- Runs every TOKEN_REFRESH_INTERVAL (7200 seconds = 2h from env)
- Checks expiry for all tokens
- If within 7 days of expiry → refresh proactively
- Meta long-lived token refresh:
  `GET /oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={current}`
- LinkedIn token refresh:
  `POST https://www.linkedin.com/oauth/v2/accessToken` with grant_type=refresh_token
- If refresh fails → log error + send dashboard alert (write to a notifications table)
- Logs every refresh attempt (success/failure) to token_refresh_log table

---

### 3. Content Generator (OpenRouter call wrapper)
**Path:** `backend/content/generator.py`

You own the OpenRouter API call. Agent A owns the prompt assembly.

Build:
- `call_openrouter(system_prompt, user_prompt, model=None)` → returns list of post variant strings
- model defaults to OPENROUTER_DEFAULT_MODEL env var (Llama 4 Scout for speed)
- Use OPENROUTER_DEEP_MODEL (Claude-class) for complex pieces when explicitly requested
- Headers: `Authorization: Bearer {OPENROUTER_API_KEY}`, `HTTP-Referer: https://oybit.nyvora.com`, `X-Title: Oybit`
- Request 5–20 variants in a single call using n parameter or structured output
- Implement retry logic (3 attempts, exponential backoff)
- Parse response → return clean list of variant strings

Also build:
- `repurposer.py` — takes blog post content or vlog transcript → calls OpenRouter → returns dict of platform-native slices {linkedin: str, instagram_personal: str, instagram_brand: str, facebook: str}
- `bulk.py` — takes list of topic briefs → batches generation calls → returns full week/month content plan

---

### 4. Render Engine
**Path:** `backend/render_engine/`

**`carousel.py`**
- Takes: template_name, context dict (slide_content[], brand_colors, fonts, account_type)
- Loads Jinja2 template from `render_engine/templates/`
- Renders each slide as HTML → Playwright screenshots at 1080×1080
- Returns: list of file paths to JPEG images
- Async implementation (async def render_carousel)
- Install Playwright chromium: `playwright install chromium`
- Output directory: RENDER_OUTPUT_DIR from env (/tmp/oybit_renders)
- Clean up temp files after upload

Build HTML templates for each account type:
- `templates/carousel_personal_ig.html` — casual, Ahmad's brand colors, clean
- `templates/carousel_brand_ig.html` — Nyvora colors, professional, product-forward
- `templates/carousel_linkedin.html` — minimal, professional, black/white/accent
- `templates/carousel_base.html` — base template with CSS variables others extend
- Template context variables: {{slide_headline}}, {{slide_body}}, {{slide_number}}, {{total_slides}}, {{brand_color_primary}}, {{brand_color_secondary}}, {{font_family}}, {{logo_url}} (if brand)

**`video.py`**
- Takes: composition_id, props dict (content, colors, timing, account_type), output_path
- Calls Remotion render via subprocess:
  ```python
  subprocess.run(["npx", "remotion", "render", "src/index.tsx", composition_id, output_path, "--props", json.dumps(props)])
  ```
- Post-processes with ffmpeg for platform compliance:
  - Instagram Reels: scale to 1080×1920 (9:16), h264, faststart
  - Facebook video: scale to 1280×720 (16:9), h264
- Returns: final .mp4 path

Build Remotion compositions at `render_engine/templates/video/`:
- `PersonalBrand.tsx` — Ahmad personal style: kinetic typography, dark background, accent colors, hook text animation, fast cuts
- `NyvoraBrand.tsx` — Nyvora brand style: clean minimal, product-forward, brand colors
- `src/index.tsx` — Remotion entry point, registers all compositions

**`image.py`**
- Takes: prompt_text, width, height, output_path
- Calls Pollinations.ai (no API key needed):
  ```python
  url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={w}&height={h}&nologo=true&model=flux&enhance=true"
  ```
- Downloads image → saves to output_path
- Returns: local file path

**`prompt_builder.py`** (image prompt builder — separate from Agent A's text prompt builder)
- Reads persona.md visual identity section (colors, style, aesthetic)
- Takes: post_brief, platform, account_type, aspect_ratio
- Returns: detailed 150–200 word image generation prompt
- Must include: style, mood, colors, composition, subject matter, quality markers

---

### 5. Scheduler
**Path:** `backend/scheduler_worker/`

**`queue.py`**
- SQLite queue at `/data/queue.db`
- Schema: id, post_id, account, scheduled_at, status (pending|running|done|failed), attempts, last_error, created_at
- Methods: add_job(post_id, account, scheduled_at), get_due_jobs(), mark_running(id), mark_done(id), mark_failed(id, error), increment_attempts(id)

**`dispatcher.py`**
- Called every SCHEDULER_INTERVAL (300s = 5min from env)
- Gets all due jobs (scheduled_at <= now, status=pending, attempts < 3)
- For each job: mark_running → call publishers/dispatcher.py → mark_done or mark_failed
- Retry logic: if failed and attempts < 3 → reschedule with backoff (5min, 15min, 45min)
- After 3 failures: mark failed_final → write to dashboard alerts

**`cron.py`**
- Main loop: runs dispatcher every SCHEDULER_INTERVAL seconds
- Uses Python `schedule` library
- Handles graceful shutdown on SIGTERM (Railway sends this before restart)

---

### 6. Analytics Aggregator
**Path:** `backend/analytics/`

**`aggregator.py`**
- Called daily by analytics_worker.py at 6AM
- For each published post (from last 48h+), polls platform analytics:
  - Instagram (personal + brand): `GET /{ig-media-id}/insights?metric=reach,impressions,likes,comments,shares,saved`
  - Facebook: `GET /{post-id}/insights?metric=post_impressions,post_reach,post_reactions_by_type_total,post_shares`
  - LinkedIn: `GET /v2/socialActions/{post-urn}` → likes + comments
- Creates PostAnalytics record per post
- Marks post as analytics_collected=True after first successful pull

**`scorer.py`**
- Takes PostAnalytics record → computes engagement score
- Formula (as defined by Agent A, implemented here):
  `score = saves*5 + shares*3 + comments*2 + follows*5`
- Updates Post record with engagement_score
- Tags post with hook_type, topic_pillar, format (if not already tagged)
- Sends tagged post data to PatternDB (Agent A's table — call via internal API endpoint)

**`pattern_detector.py`** (lightweight version here — deep analysis is Agent A)
- Runs after aggregator completes
- Basic pattern: find top 5 posts by engagement_score in last 30 days
- Sends summary to Agent A's learning_engine via internal API call
- Does NOT update persona.md — that's Agent A's job

---

### 7. Reply Manager
**Path:** `backend/reply_manager/`

**`monitor.py`**
- Polls comment feeds for all 4 accounts after each post (and periodically)
- Instagram: `GET /{ig-media-id}/comments?fields=id,text,username,timestamp`
- Facebook: `GET /{post-id}/comments?fields=id,message,from,created_time`
- LinkedIn: `GET /v2/socialActions/{post-urn}/comments`
- Saves new comments to Reply table
- Classifies comment type: praise | question | criticism | spam | debate (simple keyword + OpenRouter classification)
- Skips spam automatically

**`drafter.py`**
- Takes Reply record + persona.md (reads engagement style section)
- Calls OpenRouter to draft reply in Ahmad's voice
- Applies per-account tone: LinkedIn replies more considered, IG replies more casual
- Returns draft reply text
- Does NOT send — creates Reply record with status=pending_approval

**`sender.py`**
- Takes approved Reply record
- Routes to correct platform API:
  - Instagram: `POST /{ig-comment-id}/replies?message={text}`
  - Facebook: `POST /{comment-id}/comments?message={text}`
  - LinkedIn: `POST /v2/socialActions/{post-urn}/comments`
- Updates Reply record with status=sent + sent_at timestamp

---

### 8. Trend Aggregator
**Path:** `backend/intelligence/trend_aggregator.py`

(This is the lightweight trend collection — MiroFish deep intelligence is Agent A)

- Runs daily at TREND_RUN_HOUR (7AM from env)
- Collects: Google Trends for keywords from persona.md, Reddit top posts, platform hashtags
- Saves raw signals to TrendSignal table
- Merges with MiroFish output to give Opportunity Detector full picture

---

### 9. API Endpoints (implement in `backend/api/`)

```
# Auth
POST   /api/auth/login
POST   /api/auth/refresh
GET    /api/auth/me

# Content
POST   /api/content/generate          # Assembles prompt (Agent A) + calls OpenRouter (you)
POST   /api/content/repurpose          # Blog/vlog → platform slices
POST   /api/content/bulk               # Generate week/month of content
GET    /api/content/drafts             # List all draft posts
PATCH  /api/content/:post_id           # Edit draft
POST   /api/content/:post_id/approve   # Move to scheduler
DELETE /api/content/:post_id           # Delete

# Scheduler
GET    /api/scheduler                  # Get calendar (posts by date/account)
POST   /api/scheduler/schedule         # Schedule a post
PATCH  /api/scheduler/:job_id          # Reschedule
DELETE /api/scheduler/:job_id          # Remove from queue

# Analytics
GET    /api/analytics/overview         # Cross-account summary
GET    /api/analytics/posts            # Per-post performance
GET    /api/analytics/growth           # Follower growth over time
GET    /api/analytics/top              # Best performing content

# Replies
GET    /api/replies                    # Pending comment queue
POST   /api/replies/:reply_id/approve  # Send AI draft reply
PATCH  /api/replies/:reply_id          # Edit before sending
POST   /api/replies/:reply_id/skip     # Skip comment

# Settings
GET    /api/settings/accounts          # Account connection status
POST   /api/settings/accounts/:name/reconnect  # Trigger re-auth
GET    /api/settings/automation        # Automation level per account
PATCH  /api/settings/automation        # Update automation level

# Internal (used between agents via API — not exposed to frontend)
POST   /api/internal/pattern-update    # Agent A calls this to receive PatternDB data
POST   /api/internal/gate-signal       # Pre-publish gate sends early signal to learning engine
```

---

### 10. Frontend Dashboard
**Path:** `frontend/`

Build the entire frontend. Next.js + React + Tailwind.

**Pages:**

`/` (Dashboard home)
- Today's post schedule (all 4 accounts)
- MiroFish intelligence feed (top 3 narratives with timing)
- Engagement summary (last 7 days, per account)
- Quick alerts (token status, failed posts, pending approvals)

`/studio` (Content Studio)
- Topic brief input OR AI-suggested briefs from MiroFish feed
- Generated candidates displayed as cards with scoring badges (T/H/P scores)
- Brand Voice Guardian result shown per card (pass/near-pass/fail)
- Pre-publish gate result shown after approval (pass/fail/delay + confidence)
- Approve → moves to calendar

`/calendar` (Scheduler)
- Drag-drop calendar view (week/month)
- Posts shown per account with color coding
- Drag to reschedule
- Click to edit/delete

`/analytics` (Analytics)
- Per-account engagement charts (reach, engagement score over time)
- Follower growth chart per account
- Top posts table (sorted by engagement score)
- Pattern insights panel (what's working, what's not)

`/intelligence` (MiroFish Feed)
- Today's narrative forecast cards
- Each card: topic, confidence score, timing recommendation, framing suggestion
- One-click → generates content from this narrative
- Trend signals sidebar (Google Trends + Reddit hot)

`/persona` (Persona Viewer)
- Render persona.md as a readable dashboard (not raw markdown)
- Edit sections inline
- Export button (downloads persona.md)
- Simulation log viewer (last 20 entries, append-only view)
- Strategy history timeline

`/replies` (Reply Manager)
- Pending comments queue across all 4 accounts
- Comment + AI draft reply side by side
- Approve / Edit / Skip actions
- Account filter

`/settings` (Settings)
- Account connections with status indicators (green/red + expiry countdown)
- Reconnect buttons per account
- Automation level selector per account (manual / semi / full-auto)
- Reply mode selector per account

**Components to build:**
- `ContentCard` — draft post card with scoring badges, platform icon, account label, approve/reject actions
- `ScoringBadge` — shows T, H, P scores as colored pills
- `GateBadge` — pre-publish gate result (pass=green, fail=red, delay=amber + recommended time)
- `MiroFishCard` — narrative forecast card with confidence meter
- `AccountStatus` — token health indicator per account
- `EngagementChart` — recharts line chart for engagement over time
- `CalendarView` — drag-drop post calendar

---

### 11. Workers
**Path:** `workers/`

**`scheduler_worker.py`**
- Runs continuously (loop every SCHEDULER_INTERVAL seconds)
- Calls `backend/scheduler_worker/cron.py`

**`analytics_worker.py`**
- Runs daily at ANALYTICS_RUN_HOUR (6AM from env)
- Calls `backend/analytics/aggregator.py` for all posts with published_at > 48h ago

**`trend_worker.py`**
- Runs daily at TREND_RUN_HOUR (7AM from env)
- Calls `backend/intelligence/trend_aggregator.py`

**`token_refresher.py`**
- Runs every TOKEN_REFRESH_INTERVAL seconds (7200 = 2h from env)
- Calls `backend/token_store/refresher.py`

---

## Your Database Models (coordinate with Agent A)

```python
class Post(Base):
    id, account, content_text, media_urls, status,
    hook_type, topic_pillar, format,
    score_topicality, score_hook, score_persona, score_total,
    mirofish_gate_result, mirofish_confidence, gate_early_signal,
    engagement_score, analytics_collected,
    scheduled_at, published_at, platform_post_id, created_at

class PostAnalytics(Base):
    id, post_id, account, reach, impressions, likes, comments,
    shares, saves, follows, clicks, engagement_score, measured_at

class Reply(Base):
    id, post_id, account, platform_comment_id, comment_text,
    comment_type, draft_reply, status, sent_at, created_at

class TrendSignal(Base):
    id, source, topic, score, raw_data, collected_at

class SchedulerJob(Base):
    id, post_id, account, scheduled_at, status, attempts, last_error, created_at

class TokenRefreshLog(Base):
    id, account, token_type, success, error_message, refreshed_at

class Notification(Base):
    id, type, message, read, created_at
```

---

## Dependencies (add to requirements.txt)

```
playwright
jinja2
httpx
cryptography
schedule
praw
feedparser
```

And for Node (package.json in render_engine/templates/video/):
```json
{
  "dependencies": {
    "remotion": "^4.0.0",
    "@remotion/cli": "^4.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
```

---

## Coordination Notes for Agent B

- Do NOT touch anything in `backend/intelligence/mirofish/` — Agent A's
- Do NOT touch `backend/persona_engine/` — Agent A's
- Do NOT touch `backend/brand_voice_guardian/` — Agent A's
- Do NOT touch `backend/feedback_loop/learning_engine.py` or `persona_patcher.py` — Agent A's
- Do NOT touch `backend/onboarding/` — Agent A's
- Coordinate on `backend/db/models.py` — you define your models, Agent A defines theirs
- Coordinate on `backend/content/generator.py` — Agent A writes prompt assembly, you write the OpenRouter call
- When scoring posts: call `/api/internal` endpoints to trigger Agent A's scoring + guardian
- Never write directly to persona.md or simulation_log.md — those are Agent A's exclusive files

---

---

# SHARED: Both Agents Read This

## Build Order (follow this sequence)

**Phase 1 — Foundation (do this first, both agents in parallel)**

Agent A:
1. `backend/db/models.py` (your models only)
2. `backend/persona_engine/builder.py`
3. `backend/onboarding/questions.py`

Agent B:
1. `backend/db/models.py` (your models only)
2. `backend/token_store/store.py`
3. `backend/token_store/refresher.py`

**Phase 2 — Core Systems**

Agent A:
4. `backend/onboarding/sim_engine.py`
5. `backend/onboarding/calibration.py`
6. `backend/intelligence/content_dna_checker.py`
7. `backend/intelligence/opportunity_detector.py`

Agent B:
4. `backend/publishers/instagram_personal.py`
5. `backend/publishers/instagram_brand.py`
6. `backend/publishers/facebook.py`
7. `backend/publishers/linkedin.py`
8. `backend/publishers/dispatcher.py`

**Phase 3 — Intelligence + Rendering**

Agent A:
8. `backend/intelligence/mirofish/seed_builder.py`
9. `backend/intelligence/mirofish/graph_builder.py`
10. `backend/intelligence/mirofish/agent_spawner.py`
11. `backend/intelligence/mirofish/simulation_runner.py`
12. `backend/intelligence/mirofish/report_agent.py`
13. `backend/intelligence/mirofish/narrative_forecaster.py`
14. `backend/intelligence/scorer.py`
15. `backend/brand_voice_guardian/checker.py`
16. `backend/persona_engine/prompt_builder.py`

Agent B:
9. `backend/render_engine/image.py`
10. `backend/render_engine/prompt_builder.py`
11. `backend/render_engine/carousel.py` + HTML templates
12. `backend/render_engine/video.py` + Remotion compositions
13. `backend/content/generator.py` (OpenRouter call wrapper)
14. `backend/content/repurposer.py`
15. `backend/content/bulk.py`

**Phase 4 — Pipeline Connections**

Agent A:
17. `backend/intelligence/mirofish/pre_publish_gate.py`
18. `backend/feedback_loop/learning_engine.py`
19. `backend/feedback_loop/persona_patcher.py`
20. `backend/feedback_loop/mirofish_refiner.py`
21. `backend/persona_engine/updater.py`
22. `backend/persona_engine/rotation_trigger.py`

Agent B:
16. `backend/scheduler_worker/queue.py`
17. `backend/scheduler_worker/dispatcher.py`
18. `backend/scheduler_worker/cron.py`
19. `backend/analytics/aggregator.py`
20. `backend/analytics/scorer.py`
21. `backend/reply_manager/monitor.py`
22. `backend/reply_manager/drafter.py`
23. `backend/reply_manager/sender.py`

**Phase 5 — API + Workers + Frontend**

Both agents: implement all API endpoints listed in your section
Agent A: implement mirofish_worker.py + feedback_worker.py
Agent B: implement scheduler_worker.py + analytics_worker.py + trend_worker.py + token_refresher.py + full frontend

**Phase 6 — Integration + Testing**
Both agents: test your modules end-to-end, then test the cross-agent integration points

---

## File Ownership Reference (quick lookup)

| Path | Owner |
|---|---|
| `backend/intelligence/mirofish/` | Agent A |
| `backend/intelligence/opportunity_detector.py` | Agent A |
| `backend/intelligence/content_dna_checker.py` | Agent A |
| `backend/intelligence/scorer.py` | Agent A |
| `backend/intelligence/trend_aggregator.py` | Agent B |
| `backend/persona_engine/` | Agent A |
| `backend/onboarding/` | Agent A |
| `backend/brand_voice_guardian/` | Agent A |
| `backend/feedback_loop/` | Agent A |
| `backend/content/generator.py` (prompt logic) | Agent A |
| `backend/content/generator.py` (OpenRouter call) | Agent B |
| `backend/content/repurposer.py` | Agent B |
| `backend/content/bulk.py` | Agent B |
| `backend/publishers/` | Agent B |
| `backend/render_engine/` | Agent B |
| `backend/token_store/` | Agent B |
| `backend/scheduler_worker/` | Agent B |
| `backend/analytics/` | Agent B |
| `backend/reply_manager/` | Agent B |
| `workers/mirofish_worker.py` | Agent A |
| `workers/feedback_worker.py` | Agent A |
| `workers/scheduler_worker.py` | Agent B |
| `workers/analytics_worker.py` | Agent B |
| `workers/trend_worker.py` | Agent B |
| `workers/token_refresher.py` | Agent B |
| `frontend/` | Agent B |
| `/data/personas/ahmad/persona.md` | Agent A (exclusive write) |
| `/data/personas/ahmad/simulation_log.md` | Agent A (exclusive write, append-only) |
| `backend/db/models.py` | Both (coordinate) |

---

## Environment Variables Both Agents Need

All from Railway environment. Never hardcode. Always `os.getenv()`.

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout")
OPENROUTER_DEEP_MODEL = os.getenv("OPENROUTER_DEEP_MODEL", "anthropic/claude-sonnet-4-5")
ZEP_API_KEY = os.getenv("ZEP_API_KEY")
RENDER_OUTPUT_DIR = os.getenv("RENDER_OUTPUT_DIR", "/tmp/oybit_renders")
```

---

## The One Rule Both Agents Must Follow

**Build what is in the docs. Not what you think should be there.**

If something seems wrong or missing, add a `# TODO: confirm with Ahmad` comment and continue.
Do not redesign architecture. Do not add features not in the docs.
The spec is in the 8 markdown files. Follow it exactly.
