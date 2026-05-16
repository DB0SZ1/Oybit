# FINAL_CHECKLIST.md — Oybit Launch Readiness

> This is the last file before Oybit goes live.
> Work through every section in order. Do not skip ahead.
> Every check must pass before moving to the next section.
> The UI revamp section is mandatory — the dashboard is part of the product.

---

# PHASE 0 — MERGE AND DEDUPLICATE

Before running any checks, both agents' code must be merged into one coherent codebase.

## 0.1 — Single Base Declaration

```bash
# Search for duplicate Base declarations
grep -r "declarative_base()" backend/ --include="*.py"
```

**Expected:** Exactly ONE result → `backend/db/base.py`
**If more than one:** Delete all others, import from `backend.db.base` everywhere

---

## 0.2 — Single Config File

```bash
# Search for duplicate config/env files
find backend/ -name "config.py" | head -20
```

**Expected:** Exactly ONE `backend/config.py`
**If more than one:** Merge all env vars into the single file, delete duplicates

---

## 0.3 — Import Chain Check

```bash
python -c "from backend.db.models import *" 2>&1
python -c "from backend.main import app" 2>&1
python -c "from backend.intelligence.mirofish.narrative_forecaster import run_daily_forecast" 2>&1
python -c "from backend.publishers.dispatcher import dispatch_post" 2>&1
python -c "from backend.feedback_loop.learning_engine import run_learning_cycle" 2>&1
```

**Expected:** All five return with no output (no errors)
**If any crash:** Fix the import error before continuing. Do not proceed with broken imports.

---

## 0.4 — No Hardcoded Values

```bash
# Search for hardcoded tokens, secrets, or API keys
grep -rn "sk-" backend/ --include="*.py" | grep -v "test" | grep -v "#"
grep -rn "Bearer " backend/ --include="*.py" | grep -v "f\"Bearer" | grep -v "f'Bearer"
grep -rn "APP_SECRET\s*=" backend/ --include="*.py" | grep -v "os.getenv"
```

**Expected:** Zero results on all three
**If any found:** Replace with `os.getenv("VAR_NAME")` immediately

---

## 0.5 — No Shell=True

```bash
grep -rn "shell=True" backend/ workers/ --include="*.py"
```

**Expected:** Zero results
**If found:** Replace all `shell=True` with explicit argument list and `shell=False`

---

## 0.6 — No Unicode in Log Statements

```bash
# Check for emoji in Python files
python3 -c "
import os, re
found = []
for root, dirs, files in os.walk('backend'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, encoding='utf-8', errors='ignore') as fp:
                for i, line in enumerate(fp, 1):
                    if re.search(r'[^\x00-\x7F]', line) and ('logger' in line or 'print' in line):
                        found.append(f'{path}:{i}: {line.strip()[:80]}')
for f in found:
    print(f)
print(f'Found {len(found)} unicode in log statements')
"
```

**Expected:** 0 unicode in log statements
**If found:** Replace with ASCII descriptions

---

## 0.7 — Alembic Single Migration Head

```bash
alembic heads
```

**Expected:** Exactly ONE head listed
**If two heads:** Run `alembic merge heads -m "merge_agent_a_and_b"` then `alembic upgrade head`

---

## 0.8 — Database Migration

```bash
alembic upgrade head 2>&1
```

**Expected:** Runs cleanly, all tables created
**If errors:** Fix model conflicts before continuing

---

## 0.9 — Verify All 20 Tables Exist

```bash
python -c "
from backend.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
expected = [
    'posts', 'post_analytics', 'replies', 'scheduler_jobs',
    'token_records', 'token_refresh_logs', 'trend_signals',
    'notifications', 'worker_heartbeats', 'mirofish_runs',
    'pre_publish_gates', 'simulation_log_entries', 'pattern_db',
    'onboarding_sessions', 'audit_logs', 'waitlist_entries',
    'campaigns', 'follow_records', 'vlog_transcription_jobs',
    'account_daily_metrics'
]
missing = [t for t in expected if t not in tables]
extra = [t for t in tables if t not in expected and t != 'alembic_version']
print(f'Tables found: {len(tables)}')
print(f'Missing: {missing}')
print(f'Unexpected: {extra}')
"
```

**Expected:** Missing = [], all 20 tables present

---

---

# PHASE 1 — ENVIRONMENT AND INFRASTRUCTURE

## 1.1 — Env Vars Present

```bash
python -c "
import os
required = [
    'DATABASE_URL', 'REDIS_URL', 'SECRET_KEY', 'OPENROUTER_API_KEY',
    'ZEP_API_KEY', 'FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET',
    'INSTAGRAM_PERSONAL_ACCESS_TOKEN', 'INSTAGRAM_PERSONAL_USER_ID',
    'INSTAGRAM_BRAND_ACCESS_TOKEN', 'INSTAGRAM_BRAND_USER_ID',
    'FACEBOOK_PAGE_ACCESS_TOKEN', 'FACEBOOK_PAGE_ID',
    'LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET',
    'LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_PERSON_URN',
    'TELEGRAM_BOT_TOKEN', 'TELEGRAM_AHMAD_CHAT_ID',
    'TOKEN_ENCRYPTION_KEY', 'FRONTEND_URL',
    'PERSONA_PATH', 'QUEUE_PATH', 'RENDER_OUTPUT_DIR'
]
missing = [v for v in required if not os.getenv(v)]
present = [v for v in required if os.getenv(v)]
print(f'Present: {len(present)}/{len(required)}')
if missing:
    print(f'MISSING: {missing}')
else:
    print('ALL ENV VARS PRESENT')
"
```

**Expected:** ALL ENV VARS PRESENT

---

## 1.2 — Volume Mounts Exist

```bash
python -c "
import os
from pathlib import Path
paths = {
    'PERSONA_PATH': os.getenv('PERSONA_PATH', '/data/personas/ahmad/persona.md'),
    'QUEUE_PATH': os.getenv('QUEUE_PATH', '/data/queue.db'),
    'RENDER_OUTPUT_DIR': os.getenv('RENDER_OUTPUT_DIR', '/tmp/oybit_renders'),
}
for name, path in paths.items():
    parent = Path(path).parent
    exists = parent.exists()
    print(f'  {\"OK\" if exists else \"FAIL\"} {name}: {parent}')
"
```

**Expected:** All OK — if FAIL, Volume is not mounted. Fix Railway/Render Volume config.

---

## 1.3 — Redis Connection

```bash
python -c "
import redis, os
r = redis.from_url(os.getenv('REDIS_URL'))
r.ping()
print('Redis: OK')
"
```

**Expected:** Redis: OK

---

## 1.4 — Playwright Chromium Installed

```bash
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('about:blank')
    browser.close()
    print('Playwright Chromium: OK')
"
```

**Expected:** Playwright Chromium: OK
**If fails:** Run `playwright install chromium --with-deps`

---

## 1.5 — Node.js and Remotion Available

```bash
node --version
npx remotion --version 2>/dev/null || echo "Remotion not installed"
ffmpeg -version | head -1
```

**Expected:** Node version printed, Remotion version printed, ffmpeg version printed
**If Remotion missing:** `cd render_engine/templates/video && npm install`

---

## 1.6 — GraphRAG Initialized

```bash
python -c "
from pathlib import Path
graphrag_config = Path('backend/intelligence/mirofish/graphrag_project/settings.yaml')
if graphrag_config.exists():
    print('GraphRAG: OK — config exists')
else:
    print('GraphRAG: FAIL — run python scripts/setup_graphrag.py')
"
```

**Expected:** GraphRAG: OK

---

## 1.7 — Deep Health Check

```bash
# Start the API server first
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
sleep 3

curl -s http://localhost:8000/health | python -m json.tool
```

**Expected:** JSON response with all checks showing "ok"
**Fail condition:** Any check shows "FAIL" — fix that specific component

---

---

# PHASE 2 — REAL PLATFORM API VERIFICATION

**These hit real platform APIs. Run them once. Fix any failures before proceeding.**

## 2.1 — Instagram Personal Account

```bash
python scripts/tests/test_real_api_calls.py --account instagram_personal
```

**What it checks:**
- Token is valid and not expired
- Account is Business or Creator type (not personal — personal accounts cannot use Graph API)
- Account is linked to a Facebook Page
- Can read account info (username, follower count)
- instagram_content_publish permission is granted
- Can create a media container (dry run — no actual publish)

**Expected output:**
```
OK  Token valid
OK  Account type: BUSINESS
OK  Linked to Facebook Page: [page name]
OK  Username: @[handle]
OK  Followers: [count]
OK  Permission: instagram_content_publish — granted
OK  Container creation: dry run succeeded
Instagram Personal: ALL CHECKS PASSED
```

**If token expired:** Run `python scripts/refresh_token.py --account instagram_personal`
**If wrong account type:** Go to Instagram app → Settings → Account → Switch to Professional Account → Creator or Business

---

## 2.2 — Instagram Brand Account

```bash
python scripts/tests/test_real_api_calls.py --account instagram_brand
```

Same checks as personal. Must use separate token (INSTAGRAM_BRAND_ACCESS_TOKEN).

**Critical check:** Verify brand token is NOT the same as personal token:
```bash
python -c "
import os
personal = os.getenv('INSTAGRAM_PERSONAL_ACCESS_TOKEN', '')[:20]
brand = os.getenv('INSTAGRAM_BRAND_ACCESS_TOKEN', '')[:20]
if personal == brand:
    print('FAIL: Same token used for both accounts — will post to wrong account')
else:
    print('OK: Tokens are different')
"
```

---

## 2.3 — Facebook Page

```bash
python scripts/tests/test_real_api_calls.py --account facebook
```

**What it checks:**
- Page token is valid
- pages_manage_posts permission granted
- Can read page info (name, fan count)
- Can create a draft post without publishing (using unpublished=true)

---

## 2.4 — LinkedIn

```bash
python scripts/tests/test_real_api_calls.py --account linkedin
```

**What it checks:**
- Access token valid
- w_member_social scope granted
- Can read profile (first name, last name, ID)
- Person URN matches actual account
- Can create a draft ugcPost (using lifecycleState: DRAFT)

**Verify person URN:**
```bash
python -c "
import requests, os
response = requests.get(
    'https://api.linkedin.com/v2/me',
    headers={'Authorization': f'Bearer {os.getenv(\"LINKEDIN_ACCESS_TOKEN\")}'}
)
data = response.json()
actual_urn = f'urn:li:person:{data[\"id\"]}'
configured_urn = os.getenv('LINKEDIN_PERSON_URN')
if actual_urn == configured_urn:
    print(f'OK  URN matches: {actual_urn}')
else:
    print(f'FAIL URN mismatch:')
    print(f'     Actual:     {actual_urn}')
    print(f'     Configured: {configured_urn}')
    print(f'     Fix: set LINKEDIN_PERSON_URN={actual_urn}')
"
```

---

## 2.5 — OpenRouter API

```bash
python -c "
import requests, os
response = requests.post(
    'https://openrouter.ai/api/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {os.getenv(\"OPENROUTER_API_KEY\")}',
        'Content-Type': 'application/json'
    },
    json={
        'model': os.getenv('OPENROUTER_DEFAULT_MODEL', 'meta-llama/llama-4-scout'),
        'messages': [{'role': 'user', 'content': 'Reply with exactly: OYBIT_TEST_OK'}],
        'max_tokens': 20
    }
)
data = response.json()
if 'choices' in data:
    content = data['choices'][0]['message']['content']
    print(f'OK  OpenRouter response: {content}')
    print(f'OK  Model used: {data.get(\"model\", \"unknown\")}')
else:
    print(f'FAIL OpenRouter error: {data}')
"
```

**Expected:** OYBIT_TEST_OK in response

---

## 2.6 — Telegram Bot

```bash
python -c "
import requests, os
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_AHMAD_CHAT_ID')

# Test bot info
bot_info = requests.get(f'https://api.telegram.org/bot{bot_token}/getMe').json()
if bot_info.get('ok'):
    print(f'OK  Bot connected: @{bot_info[\"result\"][\"username\"]}')
else:
    print(f'FAIL Bot token invalid: {bot_info}')

# Send test alert to Ahmad
if chat_id:
    send = requests.post(
        f'https://api.telegram.org/bot{bot_token}/sendMessage',
        json={'chat_id': chat_id, 'text': '[OYBIT] System check — all good. This confirms alerts are working.'}
    ).json()
    if send.get('ok'):
        print(f'OK  Alert sent to Ahmad — check Telegram to confirm received')
    else:
        print(f'FAIL Could not send alert: {send}')
"
```

**Ahmad must confirm he received the Telegram message before continuing.**

---

---

# PHASE 3 — MIROFISH INTEGRATION VERIFICATION

## 3.1 — GraphRAG Seed Collection

```bash
python -c "
from backend.intelligence.mirofish.seed_builder import collect_seeds
seeds = collect_seeds(['software development', 'startup', 'Nigeria tech', 'automation'])
print(f'Seeds collected: {len(seeds)}')
if len(seeds) < 5:
    print('WARNING: Very few seeds — check RSS/Reddit connectivity')
else:
    print('OK  Seed collection working')
    for s in seeds[:3]:
        print(f'    [{s[\"source\"]}] {s[\"title\"][:60]}')
"
```

**Expected:** 10+ seeds from multiple sources

---

## 3.2 — Knowledge Graph Build

```bash
python -c "
from backend.intelligence.mirofish.seed_builder import collect_seeds
from backend.intelligence.mirofish.graph_builder import build_knowledge_graph
import time

seeds = collect_seeds(['developer tools', 'SaaS', 'Nigeria'])[:10]
print(f'Building graph from {len(seeds)} seeds...')
start = time.time()
graph = build_knowledge_graph(seeds)
elapsed = time.time() - start

entities = len(graph.get('entities', []))
relationships = len(graph.get('relationships', []))
communities = len(graph.get('communities', []))

print(f'OK  Graph built in {elapsed:.1f}s')
print(f'    Entities: {entities}')
print(f'    Relationships: {relationships}')
print(f'    Communities: {communities}')

if entities == 0:
    print('FAIL: No entities extracted — check GraphRAG initialization')
if communities == 0:
    print('WARN: No communities detected — graph may be too sparse')
"
```

**Expected:** Entities > 5, Communities > 0, runtime under 120s

---

## 3.3 — Narrative Forecaster Output Quality

```bash
python -c "
from backend.intelligence.mirofish.narrative_forecaster import generate_narratives
from pathlib import Path
import json

print('Running narrative forecast (this takes 2-5 minutes on first run)...')
results = generate_narratives(
    niche_keywords=['developer', 'SaaS', 'automation', 'Nigeria'],
    persona_path=Path('persona/ahmad.md')
)

print(f'Narratives found: {len(results)}')
for i, n in enumerate(results[:3], 1):
    print(f'  Narrative {i}:')
    print(f'    Topic: {n.get(\"topic\", \"unknown\")[:80]}')
    print(f'    Confidence: {n.get(\"confidence\", 0):.2f}')
    print(f'    Framing: {n.get(\"framing_suggestion\", \"none\")[:60]}')
    print()

if len(results) == 0:
    print('FAIL: No narratives generated')
    print('     Check: Are seeds being collected?')
    print('     Check: Is GraphRAG initialized?')
    print('     Check: Is ZEP_API_KEY valid?')
elif results[0].get('confidence', 0) < 0.3:
    print('WARN: Low confidence narratives — MiroFish may need more data')
    print('     This is normal on first run. Improves after 2 weeks of data.')
else:
    print('OK  Narrative forecaster working')
"
```

**Expected:** 1+ narratives with confidence > 0.3
**First-run reality:** Confidence will likely be 0.3–0.5 — this is normal. MiroFish improves as the learning engine feeds data back.

---

## 3.4 — Pre-Publish Gate on a Test Post

```bash
python -c "
from backend.intelligence.mirofish.pre_publish_gate import run_gate

# Test with known good post (real LinkedIn post format that worked)
test_post = '''2AM. The automation SaaS just drafted a LinkedIn post with my live Paystack key in it.

The secret scan in the pipeline caught it before it hit the platform.

Building your own tools means you are the first user — and the first line of defense.'''

result = run_gate(test_post, 'linkedin')
print(f'Gate decision: {result[\"decision\"]}')
print(f'Confidence: {result[\"confidence\"]:.2f}')
if result.get('failure_reason'):
    print(f'Reason: {result[\"failure_reason\"]}')
print(f'Early learning signal: {result.get(\"early_learning_signal\", {})}')

if result['decision'] == 'pass':
    print('OK  Gate working — known good post passed')
elif result['decision'] == 'delay':
    print('OK  Gate working — timing adjustment suggested')
else:
    print('WARN: Known good post was blocked — review gate thresholds')
"
```

**Expected:** decision = pass or delay for this known good post
**If blocked:** Check gate confidence thresholds — may need tuning for cold start

---

## 3.5 — Full MiroFish Daily Pipeline Run

```bash
python workers/mirofish_worker.py --run-now 2>&1 | tail -50
```

**Watch for:**
- `seed collection: X seeds` — should be 10+
- `graph built: X entities` — should be 5+
- `narratives forecast: X topics` — should be 1+
- `worker_heartbeat: mirofish` — confirms heartbeat written
- No CRITICAL or ERROR level log entries

**Expected runtime:** 3–15 minutes
**If crashes:** Check logs for specific error. Most common: Zep API rate limit or GraphRAG config missing

---

---

# PHASE 4 — CONTENT PIPELINE INTEGRATION

## 4.1 — Persona File Exists and Is Valid

```bash
python -c "
from pathlib import Path
import os

persona_path = Path(os.getenv('PERSONA_PATH', 'persona/ahmad.md'))
sim_log_path = persona_path.parent / 'simulation_log.md'

if not persona_path.exists():
    print('FAIL: persona.md not found')
    print('     Run Ahmad onboarding first: GET /api/onboarding/stage/1')
else:
    content = persona_path.read_text(encoding='utf-8')
    sections = ['Identity', 'Voice', 'Audience', 'Content Pillars', 'Engagement']
    missing = [s for s in sections if s not in content]
    if missing:
        print(f'FAIL: persona.md missing sections: {missing}')
    else:
        word_count = len(content.split())
        print(f'OK  persona.md exists ({word_count} words, {len(content)} chars)')

if not sim_log_path.exists():
    print('WARN: simulation_log.md not found (expected after onboarding stage 2)')
else:
    size = sim_log_path.stat().st_size
    print(f'OK  simulation_log.md exists ({size} bytes)')
"
```

**If persona.md missing:** Ahmad must complete onboarding first. Go to `/onboarding` in dashboard.

---

## 4.2 — Content DNA Checker Integration

```bash
python -c "
from backend.intelligence.content_dna_checker import check_content_dna

# Must fail
bad = 'Working on something exciting in the tech space. Will share details soon.'
bad_result = check_content_dna(bad)
assert not bad_result.passes, f'Bad post should fail DNA check but passed: {bad_result}'
print('OK  Bad post correctly rejected by DNA checker')

# Must pass
good = 'My automation SaaS just drafted a post with my live Paystack key. The secret scan caught it before it posted. Building your own tools means you are the first line of defense.'
good_result = check_content_dna(good)
assert good_result.passes, f'Good post should pass DNA check but failed: {good_result}'
print('OK  Good post correctly passed DNA checker')
print(f'    DNA elements: system_insight={good_result.has_system_insight}, real_consequence={good_result.has_real_consequence}')
"
```

---

## 4.3 — Brand Voice Guardian Integration

```bash
python -c "
from backend.brand_voice_guardian.checker import check_brand_voice
from pathlib import Path
import os

persona_path = Path(os.getenv('PERSONA_PATH', 'persona/ahmad.md'))

# Test 1: Hard stop topic
politics_post = 'The government must do better. Here is my political opinion on the current administration.'
result = check_brand_voice(politics_post, 'linkedin', persona_path)
assert result.rejected, 'Political content should be rejected'
print('OK  Hard stop (politics) correctly rejected')

# Test 2: No DNA element
vague_post = 'Something exciting is coming. Stay tuned for more information about my project.'
result = check_brand_voice(vague_post, 'linkedin', persona_path)
assert result.rejected, 'Vague post with no DNA element should be rejected'
print('OK  Vague post correctly rejected')

# Test 3: LinkedIn too long
long_post = 'A' * 1400
result = check_brand_voice(long_post, 'linkedin', persona_path)
assert result.rejected or result.near_pass, 'Post over 1300 chars should fail or near-pass'
print('OK  LinkedIn character limit enforced')

print('Brand Voice Guardian integration: OK')
"
```

---

## 4.4 — End-to-End Content Generation

```bash
python -c "
from backend.content.generator import generate_content
from pathlib import Path
import os, time

persona_path = Path(os.getenv('PERSONA_PATH', 'persona/ahmad.md'))

brief = {
    'topic': 'I caught a security issue in my automation pipeline at 2AM — real consequence, technical mechanism',
    'dna_element': 'real_consequence',
    'target_account': 'linkedin',
    'post_type': 'text_only'
}

print('Generating content (this calls OpenRouter)...')
start = time.time()
variants = generate_content(brief, persona_path)
elapsed = time.time() - start

print(f'OK  Generated {len(variants)} variants in {elapsed:.1f}s')

for i, v in enumerate(variants[:2], 1):
    char_count = len(v)
    print(f'  Variant {i} ({char_count} chars):')
    print(f'    {v[:120]}...')
    print()

# Verify none exceed LinkedIn limit
over_limit = [v for v in variants if len(v) > 1300]
if over_limit:
    print(f'FAIL: {len(over_limit)} variants exceed LinkedIn 1300 char limit')
else:
    print('OK  All variants within LinkedIn character limit')
"
```

---

## 4.5 — Scorer Selects Top Candidates

```bash
python -c "
from backend.intelligence.scorer import score_and_select
from backend.intelligence.mirofish.narrative_forecaster import generate_narratives
from pathlib import Path
import os

persona_path = Path(os.getenv('PERSONA_PATH', 'persona/ahmad.md'))

# Mock 5 variants
variants = [
    'At 2AM last week I caught my own pipeline leaking a secret. Here is what I built to stop it.',
    'Working on something exciting. More details coming.',
    'Security matters. Every developer should scan their code.',
    'The automation ran at 2AM and found a Paystack key in its own output. I added entropy detection. Zero false positives since.',
    'Here are 5 tips for securing your API keys as a developer.'
]

results = score_and_select(variants, topicality=0.7, account='linkedin', persona_path=persona_path)

print(f'Scored {len(variants)} variants:')
for i, (score, variant) in enumerate(results, 1):
    marker = 'SELECTED' if i <= 2 else '        '
    print(f'  [{marker}] Score: {score:.3f} — {variant[:60]}...')

print()
print('OK  Scorer integration working')
"
```

---

## 4.6 — Carousel Render Test

```bash
python -c "
from backend.render_engine.carousel import render_carousel_slides
from pathlib import Path
import os, time

output_dir = Path(os.getenv('RENDER_OUTPUT_DIR', '/tmp/oybit_renders'))
output_dir.mkdir(parents=True, exist_ok=True)

test_slides = [
    {'headline': 'Test Slide 1', 'body': 'This is a test carousel slide for integration verification.', 'slide_number': 1, 'total_slides': 3},
    {'headline': 'Test Slide 2', 'body': 'Verifying that Playwright renders correctly on this deployment.', 'slide_number': 2, 'total_slides': 3},
    {'headline': 'Test Slide 3 CTA', 'body': 'If you see this, the render engine works.', 'slide_number': 3, 'total_slides': 3},
]

print('Rendering test carousel (takes 20-40s)...')
start = time.time()
image_paths = render_carousel_slides(test_slides, 'carousel_personal_ig', output_dir)
elapsed = time.time() - start

print(f'Rendered {len(image_paths)} slides in {elapsed:.1f}s')
for path in image_paths:
    size = Path(path).stat().st_size
    # Verify real JPEG header
    with open(path, 'rb') as f:
        header = f.read(3)
    is_jpeg = header == b'\xff\xd8\xff'
    print(f'  {\"OK\" if is_jpeg and size > 10000 else \"FAIL\"} {path} ({size:,} bytes, JPEG={is_jpeg})')
"
```

---

## 4.7 — Full Pipeline Dry Run

```bash
python scripts/tests/test_full_pipeline.py --dry-run 2>&1 | tail -30
```

**Expected:** All 12 pipeline steps pass with dry_run=True (publishers called but no actual API posts)

---

---

# PHASE 5 — SCHEDULER AND WORKERS INTEGRATION

## 5.1 — Scheduler Queue Operations

```bash
python -c "
from backend.scheduler_worker.queue import SchedulerQueue
from datetime import datetime, timedelta

q = SchedulerQueue()

# Test enqueue
job_id = q.add_job(post_id=99999, account='linkedin', scheduled_at=datetime.utcnow() + timedelta(minutes=1))
print(f'OK  Job enqueued: {job_id}')

# Test dequeue (should not be due yet)
due = q.get_due_jobs()
assert 99999 not in [j.post_id for j in due], 'Future job should not be due yet'
print('OK  Future jobs not dequeued early')

# Test overdue
job_id2 = q.add_job(post_id=99998, account='linkedin', scheduled_at=datetime.utcnow() - timedelta(minutes=5))
due = q.get_due_jobs()
assert any(j.post_id == 99998 for j in due), 'Past-due job should be dequeued'
print('OK  Past-due jobs correctly dequeued')

# Test stale job recovery (simulates crash)
q.mark_running(job_id2)
q.reset_stale_running_jobs(stale_threshold_minutes=0)  # treat immediately as stale
job = q.get_job_by_id(job_id2)
assert job.status == 'pending', f'Stale job should be reset to pending, got: {job.status}'
print('OK  Stale job crash recovery working')

# Cleanup
q.delete_test_jobs([99999, 99998])
print('Scheduler Queue: ALL CHECKS PASSED')
"
```

---

## 5.2 — Worker Heartbeat System

```bash
# Start each worker briefly in test mode and verify heartbeat
python -c "
from backend.utils.heartbeat import write_heartbeat, get_last_heartbeat
from datetime import datetime, timedelta

write_heartbeat('test_worker', 'ok')
last = get_last_heartbeat('test_worker')
age = (datetime.utcnow() - last).total_seconds()
assert age < 5, f'Heartbeat too old: {age}s'
print('OK  Worker heartbeat system working')
"
```

---

## 5.3 — Analytics Worker Integration

```bash
python -c "
from backend.analytics.aggregator import collect_analytics_for_account
# Collect analytics for a real published post if one exists
# Otherwise verify the function initializes without error
print('Testing analytics aggregator initialization...')
try:
    result = collect_analytics_for_account('linkedin', dry_run=True)
    print(f'OK  Analytics aggregator initialized ({result})')
except Exception as e:
    print(f'FAIL: {e}')
"
```

---

## 5.4 — Token Store Roundtrip

```bash
python -c "
from backend.token_store.store import TokenStore

store = TokenStore()

# Test encrypt/decrypt roundtrip
test_token = 'test_token_value_abc123_verification'
store.save_token('test_account', 'access_token', test_token, expiry=None)
retrieved = store.get_token('test_account', 'access_token')

assert retrieved == test_token, f'Token mismatch: {retrieved} != {test_token}'
print('OK  Token encryption roundtrip works')

# Verify raw DB value is encrypted (not plaintext)
from backend.db.session import get_db_session
from backend.db.models import TokenRecord
with get_db_session() as db:
    record = db.query(TokenRecord).filter_by(account='test_account').first()
    raw_value = record.encrypted_value
    assert test_token not in raw_value, 'Token stored in plaintext — encryption broken'
    print('OK  Token stored encrypted in DB (not plaintext)')

store.delete_token('test_account', 'access_token')
print('Token Store: ALL CHECKS PASSED')
"
```

---

## 5.5 — Sensitive Moment Detector

```bash
python -c "
from backend.intelligence.sensitive_moment_detector import check_for_sensitive_moment
from datetime import datetime

# Test with normal day
normal_result = check_for_sensitive_moment(
    narratives=[{'topic': 'AI coding tools', 'confidence': 0.8}],
    date=datetime(2026, 7, 15)  # Normal day
)
assert not normal_result.is_sensitive, 'Normal day flagged as sensitive'
print('OK  Normal day not flagged as sensitive')

# Test Nigerian independence day
independence = check_for_sensitive_moment(
    narratives=[{'topic': 'tech news', 'confidence': 0.7}],
    date=datetime(2026, 10, 1)  # Nigerian Independence Day
)
assert independence.is_holiday, 'Nigerian Independence Day not detected'
print(f'OK  Holiday detected: {independence.holiday_name}')
print(f'    Engagement modifier: {independence.engagement_modifier}')

print('Cultural Calendar integration: OK')
"
```

---

---

# PHASE 6 — LEARNING LOOP INTEGRATION

## 6.1 — Engagement Score Formula Verification

```bash
python -c "
from backend.feedback_loop.learning_engine import compute_engagement_score

# Test exact formula: saves*5 + shares*3 + comments*2 + follows*5
# With normalization: divide by (followers/1000)
saves, shares, comments, follows = 10, 5, 8, 3
followers = 500

raw_expected = 10*5 + 5*3 + 8*2 + 3*5  # = 50+15+16+15 = 96
normalized_expected = raw_expected / (followers/1000)  # = 96 / 0.5 = 192.0

actual = compute_engagement_score(
    saves=saves, shares=shares, comments=comments,
    follows=follows, followers_at_post_time=followers
)

assert abs(actual - normalized_expected) < 0.1, \
    f'Formula wrong: expected {normalized_expected}, got {actual}'
print(f'OK  Engagement score formula correct: {actual:.1f} (expected {normalized_expected:.1f})')

# Test with 0 followers (should not divide by zero)
zero_result = compute_engagement_score(saves=5, shares=2, comments=3, follows=1, followers_at_post_time=0)
assert zero_result >= 0, 'Zero followers caused error'
print('OK  Zero followers handled gracefully')
"
```

---

## 6.2 — Pattern Detection Requires Minimum Data

```bash
python -c "
from backend.feedback_loop.learning_engine import detect_patterns
from backend.db.session import get_db_session

with get_db_session() as db:
    # With less than 10 posts per combo — should return no patterns
    patterns = detect_patterns(db, min_posts=10)
    print(f'Patterns found with < 10 posts per combo: {len(patterns)}')
    print('OK  Minimum data threshold enforced (no patterns from insufficient data)')
"
```

---

## 6.3 — Persona.md Atomic Write

```bash
python -c "
from backend.utils.file_ops import atomic_write
from pathlib import Path
import tempfile, os

# Test atomic write
with tempfile.TemporaryDirectory() as tmp:
    test_path = Path(tmp) / 'test.md'
    original = '# Original Content\nThis is the original.'
    test_path.write_text(original)

    # Write new content atomically
    new_content = '# Updated Content\nThis is the updated version.'
    atomic_write(test_path, new_content)

    # Verify new content
    result = test_path.read_text()
    assert result == new_content, f'Content mismatch: {result}'
    print('OK  Atomic write successful')

    # Verify no .tmp files left behind
    tmp_files = list(Path(tmp).glob('*.tmp'))
    assert len(tmp_files) == 0, f'Temp files not cleaned up: {tmp_files}'
    print('OK  No temp files left behind')

print('Atomic write: ALL CHECKS PASSED')
"
```

---

## 6.4 — simulation_log.md Append-Only

```bash
python -c "
from backend.onboarding.calibration import append_simulation_log_entry
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmp:
    log_path = Path(tmp) / 'simulation_log.md'
    log_path.write_text('# Simulation Log\n\n## Initial entry\nContent here\n')
    initial_size = log_path.stat().st_size

    # Append entry
    append_simulation_log_entry(
        log_path=log_path,
        platform='linkedin',
        scenario_type='trending_post_reaction',
        shown_content='Test post content',
        user_reaction='Would post similar',
        user_decision='Yes',
        ai_learned='User responds to technical content with personal proof'
    )

    new_size = log_path.stat().st_size
    assert new_size > initial_size, 'Log file did not grow'
    print(f'OK  Log grew from {initial_size} to {new_size} bytes')

    # Verify original content preserved
    content = log_path.read_text()
    assert 'Initial entry' in content, 'Original content was overwritten'
    print('OK  Original content preserved (append-only)')
"
```

---

---

# PHASE 7 — INDEPENDENT VERIFICATION TESTS

These tests verify outcomes from outside the implementation. Run them after all previous phases pass.

```bash
python scripts/tests/test_independent_verification.py 2>&1
```

**Must all pass before continuing.**

If any fail — fix the underlying module, not the test.

---

---

# PHASE 8 — COMPLETE API ENDPOINT VERIFICATION

```bash
# Ensure API is running
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
sleep 3

python scripts/tests/test_api_endpoints.py 2>&1
```

**Special checks:**

```bash
# CORS is configured correctly
curl -H "Origin: https://oybit.nyvora.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8000/api/content/generate \
     -v 2>&1 | grep -i "access-control-allow"

# Health endpoint returns deep check
curl -s http://localhost:8000/health | python -m json.tool

# Rate limiting is active on generation endpoint
for i in {1..15}; do
    curl -s -o /dev/null -w "%{http_code}\n" \
         -X POST http://localhost:8000/api/content/generate \
         -H "Content-Type: application/json" \
         -d '{"topic":"test","account":"linkedin","post_type":"text_only"}'
done
# Should see 429 after rate limit threshold
```

---

---

# PHASE 9 — UI REVAMP

**This section is mandatory. The dashboard is the only interface Ahmad has with this system. It must be excellent.**

Read the frontend design skill before writing a single line of UI code:
```
/mnt/skills/user/frontend-design/SKILL.md
```

---

## 9.1 — Design Direction

Oybit is a high-intelligence autonomous system. The dashboard must communicate:
- **Power and precision** — this is a serious tool, not a toy
- **Real-time awareness** — the system is always running, always learning
- **Trust and transparency** — Ahmad needs to understand what it's doing
- **Control when needed** — one-tap actions, no friction

**Aesthetic direction:** Dark, editorial, minimal brutalism. Think mission control meets editorial design. Not corporate SaaS. Not gradient-heavy startup. Something that feels like a Bloomberg Terminal for content intelligence — dense with real information, no decorative filler.

**Color palette (mandatory — do not deviate):**
```css
:root {
  --bg-base: #0A0A0B;          /* near-black background */
  --bg-surface: #111113;       /* card/panel backgrounds */
  --bg-elevated: #18181B;      /* hover states, selected */
  --border: #222226;           /* subtle borders */
  --border-active: #3A3A42;    /* active/focused borders */

  --text-primary: #F4F4F5;     /* main text */
  --text-secondary: #A1A1AA;   /* secondary/muted text */
  --text-tertiary: #52525B;    /* timestamps, metadata */

  --accent-primary: #6366F1;   /* indigo — primary actions, scores */
  --accent-secondary: #10B981; /* emerald — success, pass, live */
  --accent-warning: #F59E0B;   /* amber — delay, warning */
  --accent-danger: #EF4444;    /* red — fail, error, blocked */
  --accent-info: #3B82F6;      /* blue — info, MiroFish */

  --font-display: 'Syne', sans-serif;     /* headers, labels */
  --font-body: 'DM Mono', monospace;      /* body text, data */
  --font-data: 'IBM Plex Mono', monospace; /* scores, numbers, code */
}
```

**Typography:**
- Import from Google Fonts: `Syne` (display), `DM Mono` (body), `IBM Plex Mono` (data)
- Never use Inter, Roboto, or system fonts
- Numbers and scores always in `IBM Plex Mono` — monospaced data deserves monospaced treatment
- Headers in `Syne 700` — gives the system-level authority feeling

---

## 9.2 — Dashboard Layout (Main Hub)

**Top bar (fixed, full width):**
- Left: OYBIT wordmark in Syne, small
- Center: System status pill — `● LIVE — 3 posts queued · MiroFish last run 2h ago`
- Right: Emergency pause button (red), notification bell, Ahmad's avatar

**Left sidebar (collapsible, 220px):**
```
INTELLIGENCE
  ↳ MiroFish Feed
  ↳ Trends

CONTENT
  ↳ Studio
  ↳ Calendar
  ↳ Approval Queue

ACCOUNTS
  ↳ LinkedIn (●)
  ↳ Instagram Personal (●)
  ↳ Instagram Brand (●)
  ↳ Facebook (●)

LEARNING
  ↳ Analytics
  ↳ Patterns
  ↳ Persona

SETTINGS
  ↳ Connections
  ↳ Automation
```
Green dot = connected, Red = needs attention

**Main area — dashboard home:**
- Top row: 4 account stat cards (followers, 7-day engagement score, posts this week)
- Middle: MiroFish narrative cards (3 wide) — today's opportunities
- Bottom left: Approval queue (posts waiting) with score badges
- Bottom right: Recent published posts with engagement scores

---

## 9.3 — Page Specifications

### MiroFish Intelligence Page (`/intelligence`)

The most visually important page. Shows what the system is "thinking."

**Layout:**
- Full-width narrative feed — each card shows:
  - Topic headline
  - Confidence score (large, `IBM Plex Mono`, colored by score)
  - Timing recommendation ("Post LinkedIn today 9AM")
  - Framing suggestion (italic, secondary text)
  - One-click "Generate from this" button
- Right sidebar: live trend signals (Google, Reddit, RSS sources listed)
- Bottom: MiroFish last run metadata (time, seeds, agents, runtime)

**Micro-interaction:** Narrative cards animate in with a subtle stagger on load. Confidence score numbers count up from 0.

---

### Content Studio (`/studio`)

**Layout:**
- Left panel: Topic brief input (freeform) OR pill selector from MiroFish narratives
- Center: Generated variants displayed as cards stacked vertically
  - Each card shows: post preview, DNA badge (which element it has), account tags
  - Score badges: T | H | P in small pills with values
  - Gate result badge: PASS (emerald) / DELAY (amber) / FAIL (red)
  - Approve / Edit / Reject actions at bottom of card
- Right panel: Active persona section — shows which pillars and voice guidelines were used

**The scoring badges:**
```
[T 0.82] [H 0.91] [P 0.77]  →  TOTAL 0.86
```
All in `IBM Plex Mono`. Color: accent-primary for high scores, warning for medium, danger for low.

---

### Calendar (`/calendar`)

**Layout:**
- Full week view by default, month toggle
- Posts shown as colored blocks per account (each account has distinct color)
- Drag to reschedule — smooth drag with ghost placeholder
- Click post to preview content, see gate result, edit
- Empty slots show "+" add button on hover
- Today highlighted with accent-primary border

---

### Analytics (`/analytics`)

**Layout:**
- Account selector tabs at top
- Large engagement score trend line chart (recharts) — 30 days
- Below: Two-column grid
  - Left: Top posts table (sorted by normalized score)
  - Right: Pattern insights ("Technical + consequence → highest saves on LinkedIn")
- Bottom: Follower growth chart with milestone markers

**The charts:**
- Dark background, accent-primary line
- Subtle grid lines in var(--border)
- Hover tooltips styled consistently
- All numbers in `IBM Plex Mono`

---

### Persona Viewer (`/persona`)

**Layout:**
- Split: left = structured sections, right = raw persona.md editor
- Left shows: voice traits as pills, content pillars as weighted bars, hard stops as red tags
- Strategy History timeline at bottom — shows each version with trigger and change
- Export button (top right), Version badge (current version number)
- Voice drift indicator: small similarity gauge (if drift detected, pulse animation on it)

---

### Approval Queue (`/approval`)

**MUST be fully mobile-optimized. Primary use case is Ahmad on phone.**

**Mobile layout (< 768px):**
- Full-screen card swipe interface
- Swipe right = approve
- Swipe left = reject
- Tap = expand to full post + edit
- Current position indicator: "3 of 7 posts"
- Score badges always visible at top of card

**Desktop layout:**
- List of pending posts
- Each row: platform icon, account, first 100 chars, score, gate badge, approve/reject buttons
- Bulk approve button at top

---

### Settings (`/settings`)

**Connections tab:**
- 4 account cards (Instagram Personal, Instagram Brand, Facebook, LinkedIn)
- Each shows: connected status (green ●), token expiry countdown, reconnect button
- Color shifts red when < 7 days to expiry

**Automation tab:**
- Per-account automation level selector (Manual / Semi / Full Auto)
- Visual indicator showing what each level means
- Stories strategy toggle
- Follow strategy toggle (disabled by default, with warning)

---

## 9.4 — Component Library

Build these shared components first — everything else uses them:

**`<ScoreBadge />`**
```jsx
// Shows T/H/P scores or total score
// Props: type ('T'|'H'|'P'|'total'), value (0-1), size ('sm'|'md'|'lg')
// Color: > 0.75 = accent-secondary, > 0.5 = accent-warning, < 0.5 = accent-danger
```

**`<GateBadge />`**
```jsx
// Shows pre-publish gate result
// Props: decision ('pass'|'delay'|'fail'|'pending'), confidence (0-1)
// PASS = emerald, DELAY = amber with clock icon, FAIL = red, PENDING = gray pulse
```

**`<AccountBadge />`**
```jsx
// Platform icon + account name pill
// Props: account ('instagram_personal'|'instagram_brand'|'facebook'|'linkedin')
// Each has distinct color: IG Personal = purple, IG Brand = pink, LinkedIn = blue, FB = indigo
```

**`<DNABadge />`**
```jsx
// Shows which Content DNA element the post contains
// Props: element ('system_insight'|'real_consequence'|'technical_mechanism'|'contradiction')
// Small pill with abbreviated label: SI | RC | TM | CT
```

**`<PersonaSection />`**
```jsx
// Renders a section of persona.md as formatted UI
// Props: section ('voice'|'pillars'|'audience'|'engagement')
```

**`<WorkerStatus />`**
```jsx
// Shows a worker's last run time and status
// Props: worker ('mirofish'|'analytics'|'feedback'|'scheduler')
// Pulses if last run > 26h ago
```

---

## 9.5 — UI Implementation Rules

**Framework:** Next.js 14 with App Router. React Server Components where possible, Client Components only for interactive elements.

**Styling:** Tailwind CSS with custom CSS variables defined in `:root`. No inline styles except for dynamic values.

**Fonts:** Load from Google Fonts in `layout.tsx`:
```tsx
import { Syne, DM_Mono, IBM_Plex_Mono } from 'next/font/google'

const syne = Syne({ subsets: ['latin'], weight: ['400', '600', '700', '800'] })
const dmMono = DM_Mono({ subsets: ['latin'], weight: ['400', '500'] })
const ibmPlexMono = IBM_Plex_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] })
```

**Animations:** Use CSS transitions for all state changes. No JS-driven animations unless complex (use framer-motion sparingly).

**Loading states:** Every async operation shows a skeleton — not a spinner. Skeletons match the shape of the content they replace.

**Error states:** Every error shows what failed and what to do. Never show "Something went wrong." Show "MiroFish run failed — Zep API unreachable. Check ZEP_API_KEY in settings."

**Empty states:** Every empty state has context. Never show blank panels. "No narratives yet — MiroFish runs at 5AM WAT. First run in 3 hours."

**Mobile breakpoints:**
- `< 768px`: Approval queue becomes swipe interface. Sidebar collapses to bottom nav.
- `768px–1024px`: Sidebar visible but compact.
- `> 1024px`: Full layout.

---

## 9.6 — Frontend Build Order

Build in this exact order:

```
1. Layout and navigation (sidebar, topbar, responsive wrapper)
2. Shared component library (ScoreBadge, GateBadge, AccountBadge, DNABadge)
3. Settings page (accounts + automation) — simplest, no real-time data
4. Persona page — static-ish, important for trust
5. Approval queue — most critical, must be mobile-first
6. Content Studio — most used page
7. Analytics page — charts and data
8. Calendar — drag-drop complexity
9. MiroFish Intelligence page — most visually impressive
10. Dashboard home (uses all other components)
```

---

---

# PHASE 10 — PRE-LAUNCH FINAL CHECKS

## 10.1 — Deployment Config Files Exist

```bash
ls -la nixpacks.toml railway.toml render.yaml
```

**Expected:** All three exist. If missing, create from deployment_and_runbook.md specs.

---

## 10.2 — No Debug Flags in Production

```bash
grep -rn "debug=True" backend/ --include="*.py"
grep -rn "DEBUG=True" backend/ --include="*.py"
grep -rn "reload=True" workers/ --include="*.py"
```

**Expected:** Zero results

---

## 10.3 — All Workers Have SIGTERM Handling

```bash
grep -rn "SIGTERM\|signal.signal" workers/ --include="*.py"
```

**Expected:** Every worker file has SIGTERM handler
**If missing:** Add to each worker:
```python
import signal, sys

def handle_sigterm(signum, frame):
    logger.info("SIGTERM received — shutting down cleanly")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
```

---

## 10.4 — keepalive_worker Configured

```bash
# Verify keepalive interval is under Render's 15min sleep threshold
grep "KEEPALIVE_INTERVAL\|14\|840" workers/keepalive_worker.py
```

**Expected:** Interval set to 840 seconds (14 minutes) — under the 15-minute sleep threshold

---

## 10.5 — Ahmad's Onboarding Is Complete

```bash
python -c "
from backend.db.session import get_db_session
from backend.db.models import OnboardingSession

with get_db_session() as db:
    sessions = db.query(OnboardingSession).all()
    completed_stages = [s.stage for s in sessions if s.completed_at]
    print(f'Completed stages: {sorted(completed_stages)}')
    if 1 not in completed_stages:
        print('FAIL: Stage 1 not completed — Ahmad must complete onboarding')
    elif 2 not in completed_stages:
        print('WARN: Stage 2 (simulation) not completed — persona will be less accurate')
    elif 3 not in completed_stages:
        print('WARN: Stage 3 (tone deep-dive) not completed')
    else:
        print('OK  Core onboarding complete (stages 1-3)')
"
```

---

## 10.6 — Bootstrap PatternDB from Existing Posts

```bash
python scripts/bootstrap_pattern_db.py
```

This seeds PatternDB from Ahmad's existing LinkedIn posts so the scorer isn't blind on day one.

---

## 10.7 — First MiroFish Run Complete

```bash
python -c "
from backend.db.session import get_db_session
from backend.db.models import MiroFishRun
from datetime import datetime, timedelta

with get_db_session() as db:
    recent = db.query(MiroFishRun).order_by(MiroFishRun.created_at.desc()).first()
    if not recent:
        print('FAIL: No MiroFish runs found')
        print('     Run: python workers/mirofish_worker.py --run-now')
    else:
        age = (datetime.utcnow() - recent.created_at).total_seconds() / 3600
        print(f'Last MiroFish run: {age:.1f}h ago')
        narratives = len(recent.narrative_output or [])
        print(f'Narratives found: {narratives}')
        if narratives == 0:
            print('WARN: Zero narratives on last run — check MiroFish logs')
        else:
            print('OK  MiroFish has run and produced narratives')
"
```

---

## 10.8 — First Post Generated and Reviewed

Before enabling automation, Ahmad must manually review and approve the first 5 generated posts.

```bash
# Generate first batch for LinkedIn
curl -X POST http://localhost:8000/api/content/generate \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Something real that happened building Oybit", "account": "linkedin", "post_type": "text_only", "urgency": "normal"}'
```

Go to `/approval` in dashboard. Review all generated posts. Ahmad approves minimum 2 before any automation runs.

---

## 10.9 — Automation Level Confirmation

Before going live, confirm automation settings:

```
LinkedIn:          Semi-auto (Ahmad approves first, then auto-posts)
Instagram Personal: Semi-auto
Instagram Brand:    Semi-auto
Facebook:          Semi-auto
```

Switch to Full Auto only AFTER 2 weeks of semi-auto running cleanly.

---

## 10.10 — Emergency Pause Test

```bash
# Verify emergency pause works
curl -X POST http://localhost:8000/api/scheduler/emergency-pause \
  -H "Authorization: Bearer $JWT_TOKEN"

# Verify all jobs paused
python -c "
from backend.scheduler_worker.queue import SchedulerQueue
q = SchedulerQueue()
paused = q.count_paused_jobs()
print(f'Paused jobs: {paused}')
"

# Unpause
curl -X POST http://localhost:8000/api/scheduler/emergency-resume \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

---

# FINAL SIGN-OFF CHECKLIST

Before going live, every item below must be checked:

```
MERGE AND STRUCTURE
[ ] Single Base declaration in codebase
[ ] Single config.py with all env vars
[ ] All 5 import chains succeed without error
[ ] No hardcoded secrets anywhere
[ ] No shell=True in any subprocess call
[ ] No unicode/emoji in log statements
[ ] Single Alembic migration head
[ ] All 20 DB tables created

INFRASTRUCTURE
[ ] All env vars present
[ ] Volume mounts accessible (persona, queue)
[ ] Redis connected
[ ] Playwright Chromium installed
[ ] Node.js + Remotion + ffmpeg available
[ ] GraphRAG initialized
[ ] Deep health endpoint returns all-OK

PLATFORM CONNECTIONS
[ ] Instagram Personal — token valid, Business account, publish permission
[ ] Instagram Brand — separate token, Business account, publish permission
[ ] Instagram accounts use different tokens (not same)
[ ] Facebook Page — page token valid, manage_posts permission
[ ] LinkedIn — access token valid, person URN correct, w_member_social scope
[ ] OpenRouter — API key valid, model responds correctly
[ ] Telegram bot — sends message to Ahmad successfully
[ ] Ahmad confirmed receiving Telegram test message

MIROFISH
[ ] Seeds collected from multiple sources
[ ] Knowledge graph builds with entities
[ ] Narrative forecaster produces output
[ ] Pre-publish gate makes decisions
[ ] Full daily pipeline runs end-to-end

CONTENT PIPELINE
[ ] persona.md exists with all 8 sections
[ ] DNA checker correctly rejects vague posts
[ ] DNA checker correctly passes posts with DNA elements
[ ] Brand Voice Guardian enforces hard stops
[ ] Brand Voice Guardian enforces LinkedIn 1300 char limit
[ ] Content generator produces variants via OpenRouter
[ ] Scorer selects top candidates
[ ] Carousel render produces valid JPEG files
[ ] Full pipeline dry run passes all 12 steps

SCHEDULER AND WORKERS
[ ] Scheduler queue enqueues and dequeues correctly
[ ] Stale job recovery works (crash simulation)
[ ] Worker heartbeat system writes to DB
[ ] Token store encrypt/decrypt roundtrip works
[ ] Cultural calendar detects Nigerian holidays
[ ] Sensitive moment detector works

LEARNING LOOP
[ ] Engagement score formula is mathematically correct
[ ] Pattern detection requires minimum 10 posts per combo
[ ] Atomic write prevents file corruption
[ ] simulation_log.md is append-only

INDEPENDENT VERIFICATION
[ ] All tests in test_independent_verification.py pass
[ ] Real API tests pass (--real-apis flag)
[ ] All API endpoint tests pass
[ ] CORS configured for Hostinger domain
[ ] Rate limiting active on generation endpoint

DEPLOYMENT
[ ] nixpacks.toml exists with all system deps
[ ] render.yaml exists
[ ] No debug flags in production code
[ ] All workers have SIGTERM handlers
[ ] keepalive_worker interval < 15 minutes

AHMAD-SPECIFIC
[ ] Onboarding stages 1-3 completed
[ ] PatternDB bootstrapped from existing LinkedIn posts
[ ] First MiroFish run complete with narratives
[ ] First 5 posts reviewed and 2+ approved manually
[ ] All accounts set to Semi-auto initially
[ ] Emergency pause/resume tested and working

UI REVAMP
[ ] Frontend design skill read before any UI code written
[ ] Color palette implemented with CSS variables
[ ] Syne, DM Mono, IBM Plex Mono fonts loaded
[ ] ScoreBadge, GateBadge, AccountBadge, DNABadge components built
[ ] All 9 pages built per specifications
[ ] Approval queue is mobile-optimized (swipe interface < 768px)
[ ] Loading states are skeletons not spinners
[ ] Error states show specific actionable messages
[ ] Empty states show context not blank panels
[ ] No Inter, Roboto, or system fonts anywhere in UI
```

---

**When every box is checked: Oybit is live.**

*"You built the product. Oybit makes the world find it."*