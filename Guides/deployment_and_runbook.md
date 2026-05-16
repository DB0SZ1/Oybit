# Oybit — Deployment & Runbook

> How to deploy, run, maintain, and debug the system. Everything needed to operate Oybit from zero.

---

## Infrastructure Overview

| Component | Where it runs | Cost |
|---|---|---|
| Backend API (FastAPI) | Railway | Free tier → $5/mo when needed |
| All background workers | Railway (separate services) | Included |
| Persona files + queue.db | Railway Volume (1GB) | Included |
| Frontend dashboard | Hostinger | Already paid ($5) |
| PostgreSQL | Railway managed DB | Free tier |
| Redis | Railway managed Redis | Free tier |
| Pollinations.ai | External (free) | $0 |
| Remotion rendering | Railway server CPU | $0 |
| Playwright rendering | Railway server CPU | $0 |
| OpenRouter (AI generation) | External | Pay per call (~$0.001/post) |
| Zep Cloud (MiroFish memory) | External | Free tier |
| MiroFish simulation | Railway server CPU | $0 |

**Total monthly cost at zero scale:** ~$0–$5

---

## First-Time Setup

### 1. Clone and configure

```bash
git clone https://github.com/ahmad/oybit
cd oybit
cp .env.example .env
# Fill in all env vars (see Environment Variables section)
```

### 2. Install dependencies

```bash
# Python backend
pip install -r requirements.txt
playwright install chromium

# Node (Remotion)
cd render_engine/templates/video
npm install

# Return to root
cd ../../..
```

### 3. Database setup

```bash
# PostgreSQL migrations
alembic upgrade head

# Seed initial data
python backend/db/seed.py
```

### 4. Connect social accounts

Run the OAuth setup script for each account:

```bash
# Meta (handles Instagram Personal, Instagram Brand, Facebook in one flow)
python scripts/connect_meta.py
# Opens browser → complete OAuth → tokens saved automatically

# LinkedIn
python scripts/connect_linkedin.py
# Opens browser → complete OAuth → token saved

# Verify all connections
python scripts/verify_connections.py
# Should output: ✅ instagram_personal ✅ instagram_brand ✅ facebook ✅ linkedin
```

### 5. Run onboarding (first time only)

```bash
# Start the API
uvicorn backend.main:app --reload

# Open dashboard in browser
# Navigate to /onboarding
# Complete Stage 1 questions (30 questions, ~15 minutes)
# Complete Stage 2 simulation scenarios (30 scenarios, ~20 minutes)
# Complete Stage 3 tone questions (30 questions, ~10 minutes)
```

After onboarding, `persona.md` and `simulation_log.md` are created at `/data/personas/ahmad/`.

### 6. First MiroFish run

```bash
python workers/mirofish_worker.py --run-now
# Takes 5–15 minutes on first run
# Outputs: narrative_forecast.json with today's opportunities
```

### 7. Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up

# All services defined in railway.toml deploy automatically
# Check Railway dashboard for service health
```

---

## Environment Variables (Full List)

```bash
# ── CORE ──────────────────────────────────────────
DATABASE_URL=postgresql://user:pass@host:port/oybit
REDIS_URL=redis://host:port
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
ENVIRONMENT=production

# ── AI GENERATION ────────────────────────────────
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_DEFAULT_MODEL=meta-llama/llama-4-scout
OPENROUTER_DEEP_MODEL=anthropic/claude-sonnet-4-5

# ── MIROFISH ──────────────────────────────────────
ZEP_API_KEY=<from zep.cloud>
MIROFISH_SIMULATION_ROUNDS=4
MIROFISH_AGENT_COUNT=500         # start low, increase with server capacity

# ── META (Instagram + Facebook) ──────────────────
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
INSTAGRAM_PERSONAL_ACCESS_TOKEN=
INSTAGRAM_PERSONAL_USER_ID=
INSTAGRAM_BRAND_ACCESS_TOKEN=
INSTAGRAM_BRAND_USER_ID=
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=

# ── LINKEDIN ──────────────────────────────────────
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_REFRESH_TOKEN=
LINKEDIN_PERSON_URN=urn:li:person:<id>

# ── BLOG INTEGRATION ──────────────────────────────
BLOG_API_URL=https://yourportfolio.com/api
BLOG_API_KEY=
BLOG_WEBHOOK_SECRET=

# ── RENDERING ─────────────────────────────────────
RENDER_OUTPUT_DIR=/tmp/oybit_renders
CAROUSEL_TEMPLATE_DIR=render_engine/templates
REMOTION_PROJECT_DIR=render_engine/templates/video

# ── WORKERS ───────────────────────────────────────
MIROFISH_RUN_HOUR=5      # 5AM WAT
TREND_RUN_HOUR=7         # 7AM WAT
ANALYTICS_RUN_HOUR=6     # 6AM WAT
SCHEDULER_INTERVAL=300   # every 5 minutes
TOKEN_REFRESH_INTERVAL=7200  # every 2 hours
FEEDBACK_RUN_DAY=sunday
FEEDBACK_RUN_HOUR=2      # 2AM WAT Sunday
```

---

## Railway Service Configuration

```toml
# railway.toml

[build]
  builder = "NIXPACKS"

# ── API ─────────────────────────────────────────
[[services]]
  name = "api"
  startCommand = "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
  healthcheckPath = "/health"
  healthcheckTimeout = 30

# ── WORKERS ─────────────────────────────────────
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

[[services]]
  name = "token-refresher"
  startCommand = "python workers/token_refresher.py"

# ── VOLUMES ─────────────────────────────────────
[[volumes]]
  name = "persona-data"
  mount = "/data/personas"
  size = "1GB"

[[volumes]]
  name = "queue-data"
  mount = "/data"
  size = "512MB"

[[volumes]]
  name = "render-temp"
  mount = "/tmp/oybit_renders"
  size = "2GB"
```

---

## Worker Schedules

| Worker | Schedule | Typical runtime |
|---|---|---|
| `scheduler_worker.py` | Every 5 min (loop) | < 30s per cycle |
| `mirofish_worker.py` | Daily 5AM WAT | 5–15 min |
| `trend_worker.py` | Daily 7AM WAT | 1–3 min |
| `analytics_worker.py` | Daily 6AM WAT | 2–5 min |
| `feedback_worker.py` | Weekly Sunday 2AM WAT | 10–20 min |
| `token_refresher.py` | Every 2h (loop) | < 1 min per cycle |

---

## Daily Operating Flow

Oybit operates fully autonomously. This is what happens every day without Ahmad touching anything:

```
05:00 WAT — mirofish_worker.py wakes up
             • Collects yesterday's seeds (news, Reddit, trends)
             • Builds knowledge graph
             • Runs swarm simulation
             • Outputs narrative_forecast.json

06:00 WAT — analytics_worker.py wakes up
             • Polls all 4 platform accounts for yesterday's post metrics
             • Computes engagement scores
             • Updates PostAnalytics records
             • Tags posts in PatternDB

07:00 WAT — trend_worker.py wakes up
             • Google Trends for niche keywords
             • Reddit hot posts scan
             • Platform hashtag signal collection
             • Merges with MiroFish forecast

08:00 WAT — Opportunity Detector processes MiroFish + trend output
             • Filters through persona.md lens
             • Applies Content DNA rule
             • Generates approved topic briefs

08:05–08:30 WAT — Content generation for the day
             • Generator produces 5–20 variants per brief
             • Scoring AI ranks candidates
             • Brand Voice Guardian filters
             • Render engine produces assets
             • Pre-publish gate runs on each post

08:30–09:00 WAT — Scheduler dispatches
             • LinkedIn post (optimal time: 09:00)
             • Instagram personal (optimal time varies by content type)
             • Instagram brand (optimal time: 12:00)
             • Facebook (optimal time: 10:00–12:00)

Throughout day — scheduler_worker.py runs every 5 min
             • Checks queue for due posts
             • Dispatches via correct publisher
             • Handles retries on failure

Throughout day — reply_manager monitors comments
             • Pulls new comments from all 4 accounts
             • Drafts AI replies using persona voice
             • Queues for Ahmad's approval (semi-auto) or sends automatically (full-auto)

Sunday 02:00 WAT — feedback_worker.py wakes up
             • Pattern detection across last week's posts
             • persona.md patched if triggers met
             • MiroFish refinement signal sent
             • PatternDB updated
```

---

## Runbook — Common Operations

### Check system health
```bash
railway logs --service api
railway logs --service scheduler-worker
railway logs --service mirofish-worker
```

### Force MiroFish run now
```bash
python workers/mirofish_worker.py --run-now
```

### Force feedback loop now
```bash
python workers/feedback_worker.py --run-now
```

### View current persona
```bash
cat /data/personas/ahmad/persona.md
```

### View simulation log (last 10 entries)
```bash
tail -100 /data/personas/ahmad/simulation_log.md
```

### Manually edit persona
```bash
# Edit directly on Railway Volume
railway shell --service api
nano /data/personas/ahmad/persona.md
# Or: use the persona editor in the dashboard
```

### Check post queue
```bash
sqlite3 /data/queue.db "SELECT * FROM scheduler_jobs WHERE status='pending' ORDER BY scheduled_at;"
```

### Retry failed post
```bash
python scripts/retry_post.py --post-id <id>
```

### Refresh a specific token manually
```bash
python scripts/refresh_token.py --account instagram_personal
python scripts/refresh_token.py --account instagram_brand
python scripts/refresh_token.py --account facebook
python scripts/refresh_token.py --account linkedin
```

### Check token expiry status
```bash
python scripts/check_tokens.py
# Output: token expiry dates for all 4 accounts + days until expiry
```

---

## Failure Handling

### Post fails to publish
- Publisher logs error with HTTP status and response body
- Job marked as `failed`, attempt count incremented
- Auto-retry up to 3 times with 5-minute backoff
- After 3 failures: post marked `failed_final`, dashboard alert shown
- Ahmad manually retries via `scripts/retry_post.py` or dashboard

### MiroFish simulation fails
- `mirofish_worker.py` catches exception, logs full trace
- Falls back to trend_worker output only (no swarm prediction)
- Content generation continues without MiroFish — uses cached last forecast
- Alert logged in dashboard

### Token expired / refresh fails
- `token_refresher.py` logs failure
- Dashboard shows red token status for affected account
- Publishing to that account suspended until token refreshed
- Ahmad re-runs OAuth flow via dashboard "Reconnect" button

### OpenRouter API error
- Exponential backoff (3 retries: 5s, 15s, 45s)
- If all fail: generation skipped for that brief, logged
- System continues with other briefs

### Railway service crashes
- Railway auto-restarts all services
- SQLite queue is persistent (Railway Volume) — no jobs lost
- persona.md and simulation_log.md on Volume — no data lost

---

## Performance Expectations

At launch (single user, 4 accounts):

| Operation | Expected time |
|---|---|
| Single post generation | 5–15 seconds |
| Carousel render (5 slides) | 20–40 seconds |
| Remotion video render (30s) | 2–5 minutes |
| MiroFish daily run | 5–15 minutes |
| Pre-publish gate | 30–90 seconds |
| Analytics pull (all 4 accounts) | 1–3 minutes |
| Full feedback cycle | 10–20 minutes |

Video rendering is the most CPU-intensive operation. Remotion uses headless Chrome to render each frame — a 30-second video at 30fps = 900 frames rendered. On Railway's free tier CPU this takes 2–5 minutes. Acceptable for overnight pre-generation. Not acceptable for urgent posts — use text or carousel format for time-sensitive content.
