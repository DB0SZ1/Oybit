# Oybit — Features

> Every module, what it does, how it works, what it produces. Scoped to Ahmad's personal system — 4 accounts, 3 platforms, single user.

---

## Module 1 — Persona Engine

**Purpose:** Build, store, and continuously update `persona.md` — the live brain read before every generation call, gate check, and learning update.

**What it contains:**
- Brand identity, mission, values, origin story
- Voice and tone: formality scale, signature phrases, vocabulary always used, vocabulary never used, punctuation style, sentence rhythm, fragment tolerance, emoji usage, humour type
- Audience: who they are, their language, their pain points, what they come for
- Content pillars: 4–6 topic buckets with posting weight per platform
- Hard stops: topics that never appear in any post
- Per-account tone modifiers: how the same voice shifts across personal IG vs brand IG vs LinkedIn
- Engagement style: how Ahmad handles praise, criticism, debate, spam
- Performance memory: top content types per account, engagement benchmarks, strategy history
- Vocabulary fingerprint: Ahmad's signature words, phrases, punctuation habits

**Triggered updates (4 triggers):**
1. After 14 days of data — pattern analysis + patch
2. Engagement score drops >20% for 5 consecutive posts — strategy rotation
3. After every 30 posts — performance memory refresh
4. AI pattern detector finds significant divergence — strategy focus rewritten

**File:** `/data/personas/ahmad/persona.md` on Railway Volume — never deleted, only updated.

---

## Module 2 — Onboarding & Simulation Engine

**Purpose:** Build the initial persona through staged questions AND continuously refine it through behavioral simulation.

**Stage 1 — Core 30 questions (required at setup)**
Identity, voice, audience basics, content goals, platform preferences. Initial `persona.md` generated after completion.

**Stage 2 — Simulation Engine (30 scenarios)**
Pulls real posts from Ahmad's target platforms based on declared niche/interests. Presents each as an interactive scenario:

- "This post is trending in your niche right now. Like, share, ignore, or create something like it?"
- "Here's a comment on a post like yours. How do you respond?"
- "This format is going viral on Instagram. Would you use it? How would you adapt it for your angle?"
- "This topic is blowing up. Does Ahmad have something to say here? What angle?"
- "A brand in your space just posted something controversial. Do you weigh in?"
- "A meme format is everywhere this week. Does your brand use it?"

Every reaction, decision, and typed response is appended to `simulation_log.md` permanently. The AI reads all decisions to infer: tone under pressure, content philosophy, engagement instincts, what Ahmad rejects instinctively vs engages with.

**Stage 3 — Tone Deep Dive (30 questions)**
Vocabulary fingerprinting, hard stop identification, punctuation preferences, sentence rhythm, slang tolerance, swearing policy.

**Stage 4 — Content Boundaries (15 questions, unlocks at 2 weeks)**
What Ahmad will never post. Politics, religion, relationship details, financial specifics. These become hard stops wired directly into Brand Voice Guardian.

**Stage 5 — Audience Empathy Map (15 questions, unlocks after 20 posts)**
Deep audience profiling — what language they use when frustrated vs inspired, what they specifically want from Ahmad, what they never want to see.

**Stage 6 — Engagement Style (10 questions, unlocks after 50 posts)**
How Ahmad handles different reply types per platform. Sets reply automation defaults per account.

**Ongoing calibration:**
After every manual post Ahmad publishes directly: "How authentically does this sound like you? (1–10, why?)" — low scores trigger targeted refinement questions. High scores reinforce current persona weights.

**`simulation_log.md` structure:**
```markdown
## Session [ISO date]

### Sim 001
Platform: LinkedIn
Shown: [actual trending post pulled from platform]
Scenario type: trending_post_reaction
User reaction: Would create something like this with my angle
Decision: Yes — create similar
What AI learned: Ahmad responds to build-speed content,
                  prefers to add personal proof over copying format directly

### Sim 002
Platform: Instagram
Shown: [comment on developer post]
Scenario type: comment_reply_test
Response typed: "Complexity is relative. I built my first API at 16..."
What AI learned: Ahmad uses personal proof not theory,
                  direct, non-defensive, credentials-first
```

This file is **append-only forever**. It is read alongside `persona.md` on every generation call.

---

## Module 3 — MiroFish Intelligence

**Purpose:** Predict which narratives are heating up in Ahmad's niche before they peak — and output what to post, when, and how to frame it.

**What MiroFish actually is:**
MiroFish is an open-source multi-agent swarm prediction engine (33K+ GitHub stars, backed by Shanda Group). It runs thousands of autonomous AI agents with distinct personalities, long-term memory, and behavioral logic through dual-platform simulations (Twitter-like + Reddit-like in parallel) to surface emergent narratives and predict social dynamics before they manifest in reality.

**The five-stage pipeline:**

**Stage 1 — Seed Ingestion**
`seed_builder.py` collects: yesterday's tech/startup/Africa/developer news via RSS, Google Trends signals for Ahmad's niche keywords, Reddit hot posts from r/entrepreneur r/webdev r/SideProject r/startups, platform hashtag signals from LinkedIn and Instagram, previous learning engine feedback signal.

**Stage 2 — Knowledge Graph Construction**
GraphRAG extracts entities (people, companies, events, concepts, controversies) and their relationships. Builds a structured knowledge graph — not flat text, a relational map of what's happening and who connects to what.

**Stage 3 — Agent Generation**
From the graph, MiroFish spawns thousands of agent personas — each with a distinct personality, background, initial stance on the topics, and social relationships with other agents. Agents represent Ahmad's actual audience: developers, founders, African tech community, indie hackers, LinkedIn professionals.

**Stage 4 — Simulation**
Agents interact across two parallel environments:
- Twitter-like: short posts, replies, reposts, hot takes
- Reddit-like: threaded discussions, longer arguments, upvotes

Over simulated rounds, narratives form, opinions polarize, certain framings dominate, counter-narratives emerge. OASIS (CAMEL-AI framework, scales to 1M agents) manages the simulation. Zep Cloud maintains persistent agent memory across rounds.

**Stage 5 — Report Generation**
ReportAgent synthesises what emerged:
- Which narratives are gaining traction
- Which framings resonated with which audience segments
- When the peak of conversation is predicted
- Which angles Ahmad specifically should take given his persona
- What NOT to post (narratives that generate backlash)

**Output to Oybit's Opportunity Detector:**
```json
{
  "trending_narratives": [...],
  "timing_predictions": {...},
  "framing_suggestions": [...],
  "avoid_angles": [...],
  "confidence_score": 0.78
}
```

**Runs:** Daily 5AM via `mirofish_worker.py` for forecasting. On-demand for pre-publish gate.

---

## Module 4 — Opportunity Detector

**Purpose:** Filter MiroFish output through Ahmad's persona lens. Not every trend is Ahmad's trend.

**The Content DNA Rule (non-negotiable hard filter):**
Every topic brief must contain at least one of:
- **System insight** — what this reveals about how something actually works
- **Real consequence** — something that happened or will happen as a result
- **Technical mechanism** — the specific thing that caused it
- **Contradiction** — something unexpected, counterintuitive, or that subverts assumption

**What gets killed:**
- "Working on something around X… will share later" — no consequence, no insight
- Generic tips without proof — no mechanism, no consequence
- Trend-chasing without angle — topical but not Ahmad
- Anything that violates a hard stop in `persona.md`

**Output:** Approved topic briefs with angle, target account(s), platform, timing recommendation, and predicted audience resonance.

---

## Module 5 — Content Generation Engine

**Purpose:** Generate 5–20 post candidates from an approved topic brief.

**How it works:**
1. `prompt_builder.py` reads full `persona.md` + `simulation_log.md` (last 10 entries) + topic brief + platform rules
2. Builds a structured generation prompt including: persona voice, platform tone modifier, content pillar, Content DNA requirement, winning post structure, hard stops
3. OpenRouter call (Llama 4 Scout for speed, Claude-class for complex pieces)
4. Returns 5–20 candidates with different hook styles, angles, and lengths

**Generation modes:**
- **Single post** — one topic, one or multiple target accounts
- **Bulk calendar** — fill a week or month of content across all 4 accounts
- **Repurpose** — blog post or vlog transcript → platform-native slices (blog post becomes LinkedIn article summary, IG carousel, Facebook post, and LinkedIn text post automatically)
- **Trend response** — urgent topic brief → immediate single generation

**Platform-specific rules applied per account:**
- LinkedIn: 1,300 char limit, no hashtag spam, thought leadership register, technical storytelling
- Instagram personal: hook in first line, casual tone, relatable, trending audio awareness for Reels
- Instagram brand: product-first, aesthetic, Nyvora voice, professional but not corporate
- Facebook: longer form acceptable, discussion-oriented, community angle

---

## Module 6 — Multi-Variant Scoring AI

**Purpose:** Score every generated candidate and select the top 1–2 for rendering.

**Formula:**
```
Score = σ(α₀ + α₁T + α₂H + α₃P)
```

- **T (Topicality)** — MiroFish trend score for this topic right now (0–1)
- **H (Hook strength)** — predicted curiosity of the opening line, measured by semantic similarity to high-performing hook patterns in PatternDB
- **P (Persona alignment)** — semantic similarity to what has historically worked for Ahmad, weighted by engagement score history in PatternDB
- **σ** — sigmoid normalisation to 0–1

Top 1–2 candidates advance to Brand Voice Guardian. All others are logged with rejection reason in the post record.

---

## Module 7 — Brand Voice Guardian

**Purpose:** Hard-filter before rendering. This is the gate that keeps the system honest.

**Checks performed:**
1. Does this sound like Ahmad? (semantic similarity to `persona.md` voice section)
2. Does it contain at least one Content DNA element?
3. Does it violate any hard stop from `persona.md`?
4. Is it platform-appropriate? (length, format, tone modifier match)
5. Brand safety: could this be misread, misrepresented, or generate backlash?

**Outcomes:**
- Pass → proceed to rendering
- Near-pass with edit suggestion → returned to generator with specific fix instruction
- Auto-reject → blocked, logged, next candidate tried

On full-auto mode, Brand Voice Guardian replaces human approval entirely. This is the trust layer.

---

## Module 8 — Format Render Engine

**Purpose:** Take the winning post and produce a publish-ready asset in the correct format.

**LinkedIn (text post):**
Structured text with line breaks, minimal formatting, no markdown. Generated directly from content engine output.

**Instagram Carousel (Playwright + Jinja2):**
```
slide copy generated (headline, body, CTA per slide)
    ↓
Jinja2 loads brand HTML template
(brand colors, fonts, layout from persona.md visual section)
    ↓
Playwright headless Chrome renders each slide at 1080×1080
    ↓
Screenshots saved as JPEG (quality 95)
    ↓
Array of image paths ready for Graph API carousel upload
```
Zero external cost. Runs entirely on Railway server.

**Remotion Video (clean motion graphics):**
```
Script + scene breakdown generated
    ↓
video.py builds Remotion composition props
(brand colors, fonts, text content, timing)
    ↓
Remotion renders React component → MP4
(kinetic typography, image sequences, brand colors, transitions)
    ↓
ffmpeg handles compression + format compliance
(aspect ratio, bitrate, codec for each platform)
    ↓
.mp4 ready for Reels/Facebook video upload
```
Style: clean, minimal, brand-forward — Linear/Vercel/Notion aesthetic. Not filmed, not cinematic. This is the style agencies charge thousands to produce. Oybit automates it for free.

**Image/Thumbnail (Pollinations.ai):**
```
prompt_builder.py reads persona.md visual identity section
+ post brief + platform spec (aspect ratio, mood)
    ↓
Constructs 200-word detailed image prompt
    ↓
HTTP call to Pollinations.ai (no API key, no cost)
→ image URL returned
    ↓
Downloaded and attached to post
```

---

## Module 9 — MiroFish Pre-Publish Gate

**Purpose:** Simulate the fully rendered post against live discourse BEFORE it goes live. The most important module in the system.

**Flow:**
```
Rendered post exists
    ↓
pre_publish_gate.py builds simulation seed:
  - rendered post text
  - current live discourse signals (latest trends, hot posts)
  - target account context
    ↓
MiroFish spawns fresh agents representing Ahmad's audience
    ↓
Agents react to the post in simulation:
  "Would you like/share/comment/ignore/criticise this?"
    ↓
ReportAgent synthesises:
  - Likely resonance level
  - Predicted saves / shares / comments
  - Risk of negative reception
  - Optimal timing if delayed
    ↓
PrePublishGate record created with result + confidence score
    ↓
Early learning signal sent immediately to Learning Engine
(this is the pre-signal — before any real engagement exists)
    ↓
PASS → Approval queue (or auto-publish if full-auto)
FAIL → Regenerate with new angle
DELAY → Reschedule to MiroFish-recommended time
```

No other content tool does this. Everything else posts and hopes. Oybit tests first.

---

## Module 10 — Scheduler

**Purpose:** Manage the post queue and dispatch at the right time.

**Features:**
- SQLite job queue with Railway Volume persistence
- Smart timing from MiroFish timing recommendations + historical per-account best times
- Timezone-aware dispatch (WAT — West Africa Time for Ahmad's audience, but configurable per account)
- Per-account automation level respected on every dispatch
- Retry logic on failure (3 attempts before marking failed)
- Drag-drop calendar interface in dashboard

---

## Module 11 — Platform Publishers (4 Accounts)

One dedicated module per account. Each handles: API calls, media upload, format compliance, rate limiting, token use, retry on failure, post ID logging for analytics linkage.

| Module | Account | Key endpoints used |
|---|---|---|
| `instagram_personal.py` | Ahmad's personal IG | Graph API: /media, /media_publish, /insights |
| `instagram_brand.py` | Nyvora brand IG | Graph API: /media, /media_publish, /insights |
| `facebook.py` | Facebook page | Graph API: /{page-id}/feed, /{page-id}/videos, /insights |
| `linkedin.py` | Ahmad's LinkedIn | UGC API: POST /v2/ugcPosts, GET /socialActions |

`dispatcher.py` routes each scheduled post to the correct publisher(s) based on the account field.

---

## Module 12 — Reply Manager

**Purpose:** Monitor comments across all 4 accounts and manage responses.

**Per-account modes (set in settings):**
- Manual — Oybit notifies, Ahmad handles entirely
- AI drafts, Ahmad approves — persona-voice draft served in dashboard, Ahmad approves or edits before send
- Fully automated — AI replies autonomously using persona.md engagement style section

All reply drafts are shaped by:
- Ahmad's engagement style (from `persona.md`)
- Platform context (LinkedIn replies are more considered; Instagram replies are more casual)
- Comment type detection (praise / question / criticism / spam / debate)

---

## Module 13 — Analytics Aggregator

**Purpose:** Pull real engagement from all 4 accounts after publishing.

**Metrics collected per post:**
- Reach, impressions, engagement rate
- Likes / reactions
- Comments (count)
- Shares / reposts
- Saves (Instagram)
- Follows gained in the 48h post-publish window
- Click-throughs (where trackable)

**Engagement Score:**
```
Score = saves×5 + shares×3 + comments×2 + follows×5
```
Saves and follows weighted highest — saves signal genuine value, follows signal conversion. Likes not included — lowest signal quality.

Post tagged internally with: hook_type, topic_pillar, format, account, MiroFish gate result, gate confidence score.

---

## Module 14 — Learning Engine

**Purpose:** Close the loop. Take two inputs, produce persona and strategy updates.

**Two inputs:**
1. **MiroFish pre-publish simulation result** (stored at gate time — the prediction)
2. **Real engagement score** (collected 48h after publish — the reality)

**Process:**
- Compute weighted engagement score
- Compare against predicted score from gate
- Tag post in PatternDB by hook_type + topic_pillar + format + account
- Pattern Detector finds signals across last 30 posts:
  - "Short hook + personal consequence → high saves on LinkedIn"
  - "Generic security tips → low follows everywhere"
  - "Abuja/Nigeria angle → strong engagement from African audience"
- `persona_patcher.py` updates `persona.md` on 4 triggers
- `mirofish_refiner.py` sends updated niche signal back to MiroFish to improve future predictions

**What gets patched in `persona.md`:**
- Performance memory table (top posts, engagement benchmarks)
- Content pillar posting weights (rebalanced based on what's actually working)
- Per-account tone adjustments (if one account's style is clearly outperforming)
- Strategy history (new version entry with trigger + change made)
- Current strategy focus + next rotation check date

---

## Module 15 — Memory System

**Three permanent layers:**

**`/data/personas/ahmad/persona.md`**
Live brain. Read before every generation call. Continuously updated. Never deleted. Version history maintained in the Strategy History section.

**`/data/personas/ahmad/simulation_log.md`**
Append-only forever. Every reaction, decision, and typed response from simulation scenarios. Never overwritten. This is the behavioral history of how Ahmad's voice was discovered and how it evolves.

**PatternDB (PostgreSQL)**
Aggregated performance data by hook_type + topic_pillar + format + account. Rolling averages updated after every learning cycle. This is what makes Oybit more accurate over time — the longer it runs, the more it knows about what actually works for Ahmad on each account.
