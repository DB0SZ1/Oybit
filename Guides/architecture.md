# Oybit — Architecture

> Full system architecture for a single-user personal content engine. No multi-tenancy. No billing layer. One persona, four accounts, three platforms.

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Python, FastAPI | Consistent with Ahmad's existing stack |
| Frontend | Next.js + React | Dashboard, calendar, analytics UI |
| Primary DB | PostgreSQL | Users, posts, analytics, patterns |
| Job Queue | SQLite (Railway Volume) | Lightweight scheduler queue |
| Cache | Redis | Rate limiting, platform API caching |
| Knowledge Graph | GraphRAG (MiroFish) | Narrative extraction from seed docs |
| Agent Memory | Zep Cloud (MiroFish) | Persistent agent memory across sim rounds |
| Simulation Engine | OASIS via MiroFish | Multi-agent swarm simulation |
| AI Generation | OpenRouter | Llama 4 Scout (speed) / Claude-class (depth) |
| Image Generation | Pollinations.ai | Free, no API key required |
| Video Generation | Remotion + ffmpeg | Free, React-based, runs on server |
| Carousel Rendering | Playwright + Jinja2 | Free, headless Chrome, 1080×1080 JPEGs |
| Deployment | Railway | Backend + all workers |
| Static Hosting | Hostinger | Frontend |
| Scheduling | Python `schedule` + Railway cron | Background workers |
| Auth | JWT | Single-user, no OAuth needed |

---

## Folder Structure

```
oybit/
│
├── backend/
│   ├── main.py                          # FastAPI entry point
│   ├── config.py                        # Env vars from Railway secrets
│   │
│   ├── api/
│   │   ├── auth.py                      # Simple JWT login (single user)
│   │   ├── persona.py                   # Read/write/export persona.md
│   │   ├── onboarding.py                # Question stages + sim engine
│   │   ├── content.py                   # Generate, repurpose, bulk drafts
│   │   ├── scheduler_api.py             # Calendar API, queue management
│   │   ├── analytics.py                 # Aggregated metrics endpoints
│   │   └── replies.py                   # Comment fetch + reply draft
│   │
│   ├── intelligence/
│   │   ├── mirofish/
│   │   │   ├── seed_builder.py          # Builds seed docs from trends + niche context
│   │   │   ├── graph_builder.py         # GraphRAG knowledge graph construction
│   │   │   ├── agent_spawner.py         # Generates agent personas from graph
│   │   │   ├── simulation_runner.py     # OASIS simulation orchestration
│   │   │   ├── report_agent.py          # Post-sim → structured narrative output
│   │   │   ├── pre_publish_gate.py      # Simulate THIS post against live discourse
│   │   │   └── narrative_forecaster.py  # Daily rising narrative detection
│   │   │
│   │   ├── opportunity_detector.py      # Filter MiroFish output through persona.md
│   │   ├── content_dna_checker.py       # Apply Content DNA Rule to topic briefs
│   │   ├── scorer.py                    # σ(α₀ + α₁T + α₂H + α₃P)
│   │   └── trend_aggregator.py          # Google Trends + Reddit + RSS + hashtags
│   │
│   ├── persona_engine/
│   │   ├── builder.py                   # Builds persona.md from onboarding answers
│   │   ├── updater.py                   # Applies feedback loop patches to persona.md
│   │   ├── prompt_builder.py            # persona.md + platform rules → AI prompt
│   │   └── rotation_trigger.py          # Detects when strategy should rotate
│   │
│   ├── onboarding/
│   │   ├── questions.py                 # Full 180Q bank (staged, all 6 stages)
│   │   ├── sim_engine.py                # Pull real posts, present scenarios, log decisions
│   │   └── calibration.py              # Post-publish authenticity rating prompts
│   │
│   ├── content/
│   │   ├── generator.py                 # OpenRouter call + persona + platform rules
│   │   ├── repurposer.py                # Blog post / vlog transcript → platform slices
│   │   ├── bulk.py                      # Calendar-fill: generate week/month of content
│   │   └── platform_rules.py           # Per-platform character limits, formats, rules
│   │
│   ├── brand_voice_guardian/
│   │   └── checker.py                   # Tone, topic limits, platform fit, brand safety
│   │
│   ├── render_engine/
│   │   ├── carousel.py                  # Playwright + Jinja2 → 1080×1080 JPEGs
│   │   ├── video.py                     # Remotion React component → MP4 via ffmpeg
│   │   ├── image.py                     # Pollinations.ai call + prompt builder
│   │   ├── prompt_builder.py            # persona.md visual identity → image prompt
│   │   └── templates/
│   │       ├── carousel_base.html       # Base HTML template with CSS vars
│   │       ├── carousel_personal_ig.html
│   │       ├── carousel_brand_ig.html
│   │       ├── carousel_linkedin.html
│   │       └── video/
│   │           ├── PersonalBrand.tsx    # Remotion composition — personal IG style
│   │           ├── NyvoraBrand.tsx      # Remotion composition — brand style
│   │           └── LinkedIn.tsx         # Remotion composition — LinkedIn style
│   │
│   ├── publishers/
│   │   ├── instagram_personal.py        # Ahmad's personal IG via Meta Graph API
│   │   ├── instagram_brand.py           # Nyvora brand IG via Meta Graph API
│   │   ├── facebook.py                  # Facebook page via Meta Graph API
│   │   ├── linkedin.py                  # LinkedIn via UGC API
│   │   └── dispatcher.py                # Routes to correct publisher(s)
│   │
│   ├── reply_manager/
│   │   ├── monitor.py                   # Polls comment feeds per account
│   │   ├── drafter.py                   # AI reply using persona voice
│   │   └── sender.py                    # Sends approved reply via platform API
│   │
│   ├── analytics/
│   │   ├── aggregator.py                # Pulls metrics from all 4 accounts
│   │   ├── scorer.py                    # Post engagement score (48h)
│   │   └── pattern_detector.py          # Finds winning patterns across posts
│   │
│   ├── feedback_loop/
│   │   ├── learning_engine.py           # Merges gate sim result + real engagement
│   │   ├── persona_patcher.py           # Writes updates to persona.md
│   │   └── mirofish_refiner.py          # Feeds signal back to MiroFish
│   │
│   ├── token_store/
│   │   ├── store.py                     # Encrypted token storage per account
│   │   └── refresher.py                 # Auto-refresh before expiry
│   │
│   ├── scheduler_worker/
│   │   ├── queue.py                     # SQLite job queue read/write
│   │   ├── dispatcher.py                # Reads queue → triggers publisher
│   │   └── cron.py                      # Schedule config
│   │
│   └── db/
│       ├── models.py                    # SQLAlchemy models
│       ├── migrations/                  # Alembic
│       └── seed.py                      # Dev data
│
├── frontend/
│   ├── pages/
│   │   ├── index.tsx                    # Dashboard home
│   │   ├── studio/                      # Content Studio
│   │   ├── calendar/                    # Scheduler + drag-drop calendar
│   │   ├── analytics/                   # Per-account + cross-account metrics
│   │   ├── intelligence/                # MiroFish narrative feed
│   │   ├── persona/                     # persona.md viewer + editor
│   │   ├── onboarding/                  # Staged question flow (first run only)
│   │   └── settings/                    # Account connections, automation prefs
│   │
│   └── components/
│       ├── ContentCard/                 # Draft card — edit, approve, reject
│       ├── ScoringBadge/                # Shows T/H/P scores per candidate
│       ├── MiroFishFeed/                # Narrative forecast cards
│       ├── GateBadge/                   # Pre-publish gate result indicator
│       ├── Calendar/                    # Drag-drop scheduler
│       └── AnalyticsChart/              # Per-account engagement charts
│
├── workers/
│   ├── scheduler_worker.py              # Every 5 min — dispatch due posts
│   ├── mirofish_worker.py               # Daily 5AM — narrative forecasting
│   ├── trend_worker.py                  # Daily 7AM — trend aggregation
│   ├── analytics_worker.py              # Daily 6AM — pull platform metrics
│   ├── feedback_worker.py               # Weekly — persona patches + MiroFish refine
│   └── token_refresher.py               # Every 2h — proactive token refresh
│
├── persona/
│   ├── ahmad.md                         # The only persona. The live brain.
│   ├── simulation_log.md                # Append-only. Every decision ever made.
│   └── _template.md                     # Future brand starter (not used yet)
│
├── platforms/
│   ├── instagram_personal/
│   │   ├── strategy.md
│   │   ├── api.md
│   │   └── templates.md
│   ├── instagram_brand/
│   │   ├── strategy.md
│   │   ├── api.md
│   │   └── templates.md
│   ├── facebook/
│   │   ├── strategy.md
│   │   ├── api.md
│   │   └── templates.md
│   └── linkedin/
│       ├── strategy.md
│       ├── api.md
│       └── templates.md
│
├── intelligence/
│   ├── mirofish.md                      # MiroFish deep dive
│   ├── scoring.md                       # Scoring formula + weights
│   └── content_dna.md                   # Content DNA rule + examples
│
├── data/
│   ├── personas/ahmad/persona.md        # Railway Volume — live brain
│   ├── personas/ahmad/simulation_log.md # Railway Volume — append-only memory
│   └── queue.db                         # SQLite scheduler queue
│
└── railway.toml                         # Deployment config
```

---

## Data Models

### Post
```
id, account (personal_ig | brand_ig | facebook | linkedin),
content_text, media_urls[], status
(draft | scored | approved | scheduled | published | failed),
hook_type, topic_pillar, format (text | carousel | video | image),
score_topicality, score_hook, score_persona, score_total,
mirofish_gate_result (pass | fail | delay),
mirofish_confidence, gate_early_signal (JSON),
scheduled_at, published_at, created_at
```

### PostAnalytics
```
id, post_id, account, reach, impressions, likes, comments,
shares, saves, follows, clicks,
engagement_score (saves×5 + shares×3 + comments×2 + follows×5),
measured_at
```

### MiroFishRun
```
id, run_type (daily_forecast | pre_publish_gate),
seed_content, narrative_output (JSON),
timing_recommendations (JSON), confidence_score, created_at
```

### SimulationLogEntry
```
id, session_date, sim_number, platform, scenario_type,
shown_content, user_reaction, user_decision,
ai_learned (text), appended_at
```
(Also written to simulation_log.md on Railway Volume)

### PatternDB
```
id, account, hook_type, topic_pillar, format,
avg_engagement_score, post_count, last_updated
```

### SchedulerJob
```
id, post_id, account, scheduled_at,
status (pending | running | done | failed), attempts, last_error
```

---

## Background Workers

| Worker | Schedule | Function |
|---|---|---|
| `scheduler_worker.py` | Every 5 min | Reads SQLite queue, dispatches due posts to publishers |
| `mirofish_worker.py` | Daily 5AM | Narrative forecasting — seeds from yesterday's news/trends |
| `trend_worker.py` | Daily 7AM | Google Trends, Reddit hot, RSS, IG/LinkedIn hashtags |
| `analytics_worker.py` | Daily 6AM | Pull metrics from all 4 accounts |
| `feedback_worker.py` | Weekly Sunday 2AM | Pattern detection → persona.md patch → MiroFish signal |
| `token_refresher.py` | Every 2h | Proactive token refresh for all 4 accounts |

---

## Environment Variables

```bash
# Core
DATABASE_URL=
REDIS_URL=
OPENROUTER_API_KEY=
SECRET_KEY=

# MiroFish
ZEP_API_KEY=                   # Agent memory

# Meta (Instagram Personal + Brand + Facebook — same app)
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
INSTAGRAM_PERSONAL_TOKEN=
INSTAGRAM_PERSONAL_USER_ID=
INSTAGRAM_BRAND_TOKEN=
INSTAGRAM_BRAND_USER_ID=
FACEBOOK_PAGE_TOKEN=
FACEBOOK_PAGE_ID=

# LinkedIn
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_PERSON_URN=
```

---

## Railway Deployment

```toml
[build]
  builder = "NIXPACKS"

[[services]]
  name = "api"
  startCommand = "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"

[[services]]
  name = "scheduler-worker"
  startCommand = "python workers/scheduler_worker.py"

[[services]]
  name = "mirofish-worker"
  startCommand = "python workers/mirofish_worker.py"

[[services]]
  name = "analytics-worker"
  startCommand = "python workers/analytics_worker.py"

[[services]]
  name = "feedback-worker"
  startCommand = "python workers/feedback_worker.py"

[[services]]
  name = "trend-worker"
  startCommand = "python workers/trend_worker.py"

[[volumes]]
  mount = "/data/personas"      # persona.md + simulation_log.md
  size = "1GB"
```
