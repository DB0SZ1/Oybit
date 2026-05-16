# Oybit — How It Works

> The complete end-to-end flow. From first setup to fully autonomous publishing to self-improvement.

---

## The Complete Loop

```
┌─────────────────────────────────────────────────────────────┐
│                        SETUP (once)                         │
│                                                             │
│  Staged onboarding → 180 questions across 6 stages          │
│  Simulation engine → 30 real-post scenarios                 │
│  persona.md generated + simulation_log.md started           │
│  4 accounts connected (OAuth tokens stored encrypted)       │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │    DAILY (automated)        │
                    │                             │
                    │  5AM — MiroFish worker      │
                    │  7AM — Trend aggregator     │
                    │  6AM — Analytics worker     │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │              INTELLIGENCE LAYER               │
          │                                               │
          │  MiroFish runs swarm simulation:              │
          │  • Seed: news + RSS + Reddit + hashtags       │
          │  • GraphRAG builds knowledge graph            │
          │  • Thousands of agents simulate discourse     │
          │  • ReportAgent outputs: rising narratives,    │
          │    timing predictions, framing suggestions    │
          │                                               │
          │  Trend Aggregator collects:                   │
          │  Google Trends + Reddit hot + platform tags   │
          └───────────────────────┬───────────────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │           OPPORTUNITY DETECTOR                 │
          │                                               │
          │  Filter MiroFish output through persona.md    │
          │                                               │
          │  Content DNA Rule applied:                    │
          │  Must contain: system insight OR              │
          │  real consequence OR technical mechanism      │
          │  OR contradiction                             │
          │                                               │
          │  Output: approved topic briefs with           │
          │  angle + target account + timing              │
          └───────────────────────┬───────────────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │          CONTENT GENERATION ENGINE            │
          │                                               │
          │  Reads: persona.md (full) +                   │
          │  simulation_log.md (last 10 entries) +        │
          │  topic brief + platform rules                 │
          │                                               │
          │  Generates 5–20 candidates via OpenRouter     │
          │  (different hooks, angles, lengths)           │
          │                                               │
          │  Winning structure applied:                   │
          │  real situation → system insight →            │
          │  constraint/lesson → relatable framing →      │
          │  minimal CTA                                  │
          └───────────────────────┬───────────────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │         MULTI-VARIANT SCORING AI              │
          │                                               │
          │  Score = σ(α₀ + α₁T + α₂H + α₃P)            │
          │                                               │
          │  T = topicality (MiroFish trend score)        │
          │  H = hook strength (PatternDB benchmark)      │
          │  P = persona alignment (historical match)     │
          │                                               │
          │  Top 1–2 selected → rest logged + discarded   │
          └───────────────────────┬───────────────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │           BRAND VOICE GUARDIAN                │
          │                                               │
          │  • Sounds like Ahmad?                         │
          │  • Contains Content DNA element?              │
          │  • Violates any hard stop?                    │
          │  • Platform-appropriate?                      │
          │  • Brand safety check                         │
          │                                               │
          │  Pass → render                                │
          │  Near-pass → return with edit suggestion      │
          │  Reject → next candidate tried               │
          └───────────────────────┬───────────────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │           FORMAT RENDER ENGINE                │
          │                                               │
          │  LinkedIn → structured text post              │
          │  Instagram → Playwright + Jinja2 carousel     │
          │              (1080×1080 JPEGs, free)          │
          │  Instagram → Remotion video → MP4             │
          │              (clean motion graphics, free)    │
          │  All → Pollinations.ai thumbnail (free)       │
          │                                               │
          │  Brand colors + fonts from persona.md         │
          └───────────────────────┬───────────────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │        MIROFISH PRE-PUBLISH GATE              │
          │                                               │
          │  Rendered post → fed back into MiroFish       │
          │  "If this posts RIGHT NOW, what happens?"     │
          │                                               │
          │  Agents react: resonates / ignored / backfire │
          │  Confidence score generated                   │
          │  Early learning signal → Learning Engine now  │
          │                                               │
          │  PASS → approval queue / auto-publish         │
          │  FAIL → regenerate with new angle             │
          │  DELAY → reschedule to recommended time       │
          └───────────────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │      APPROVAL QUEUE        │
                    │                            │
                    │  Per-account setting:      │
                    │  • Full auto → skip queue  │
                    │  • Semi-auto → Ahmad sees  │
                    │    draft, approves/rejects  │
                    │  • Manual → Ahmad controls │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │         SCHEDULER          │
                    │                            │
                    │  SQLite queue dispatch     │
                    │  Smart timing from MiroFish│
                    │  Timezone-aware (WAT)      │
                    │  Every 5 min check         │
                    └─────────────┬──────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │            PLATFORM PUBLISHERS                │
          │                                               │
          │  instagram_personal.py → Ahmad's personal IG  │
          │  instagram_brand.py    → Nyvora brand IG       │
          │  facebook.py           → Facebook page        │
          │  linkedin.py           → Ahmad's LinkedIn     │
          │                                               │
          │  Post ID logged → linked to analytics         │
          └───────────────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   48 HOURS LATER           │
                    └─────────────┬──────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │           ANALYTICS AGGREGATOR               │
          │                                               │
          │  Pulls: saves, shares, comments, follows,     │
          │  reach, impressions, clicks                   │
          │                                               │
          │  Engagement Score:                            │
          │  saves×5 + shares×3 + comments×2 + follows×5  │
          │                                               │
          │  Post tagged: hook_type + topic + format      │
          └───────────────────────┬───────────────────────┘
                                  │
          ┌───────────────────────▼───────────────────────┐
          │              LEARNING ENGINE                  │
          │                                               │
          │  Input 1: MiroFish gate result (stored)       │
          │  Input 2: Real engagement score (now)         │
          │                                               │
          │  Pattern detection:                           │
          │  "Short hook + consequence = high saves"       │
          │  "Generic tips = no follows"                  │
          │  "Abuja angle = stronger African audience"    │
          │                                               │
          │  persona.md patched on 4 triggers             │
          │  PatternDB updated                            │
          │  MiroFish refinement signal sent              │
          │  simulation_log.md appended (if calibration)  │
          └───────────────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   LOOP RUNS FOREVER        │
                    │   Gets smarter every post  │
                    └────────────────────────────┘
```

---

## First Setup Flow (One Time)

```
1. Ahmad runs the app for the first time
2. Stage 1 questions (30) → initial persona.md generated
3. Simulation Engine (30 scenarios from real platform posts)
   → Ahmad reacts to each → simulation_log.md started
4. Stage 3 tone questions (30) → persona.md deepened
5. Stages 4–6 unlock progressively
6. Connect 4 accounts via OAuth
7. Set automation level per account (full auto / semi / manual)
8. First MiroFish run triggered manually
9. Dashboard live — first posts generated within hours
```

---

## The Dual Instagram Strategy

Two accounts, same platform, completely different angle:

**Personal account (`instagram_personal.py`)**
- Voice: casual, grind-mode, relatable, raw
- Content: build-in-public, personal moments, transformation stories
- Trend adaptation: YES — personal IG specifically adapts to what's trending (trending audio, trending formats, trending topics in the developer/founder space)
- Format: Reels (Remotion), carousels, casual image posts
- Tone: "18yo in Abuja shipping real products — this is what it actually looks like"

**Brand account (`instagram_brand.py`)**
- Voice: professional, product-first, Nyvora authority
- Content: product updates, milestones, clean product visuals, Nyvora narrative
- Trend adaptation: selective — only trends that fit brand positioning
- Format: carousels, clean product shots, Remotion brand videos
- Tone: "Nyvora is building Africa's AI stack"

Both accounts share the same content generation pipeline but receive different persona.md tone modifiers. The same topic generates two completely different posts depending on the target account.

---

## The Blog Integration

Ahmad's portfolio blog already has AI baked in. Oybit connects via the blog's existing API:

```
New blog post published
    ↓
Oybit detects via webhook or polling
    ↓
repurposer.py pulls full post content
    ↓
Generates platform-native slices:
  • LinkedIn: technical insight post (key lesson extracted)
  • Personal IG: behind-the-scenes story carousel
  • Brand IG: product/Nyvora angle if relevant
  • Facebook: longer-form discussion post
    ↓
Each slice goes through normal scoring → gate → publish pipeline
```

One blog post becomes 4 platform-native posts automatically. Ahmad writes once, Oybit distributes everywhere.

---

## What Ahmad Actually Does Day-to-Day

Almost nothing. Oybit is designed to run unattended.

**Ahmad's only touchpoints:**
- Occasionally edits `persona.md` when something major shifts (new product launch, direction change, strategy pivot)
- Reviews approval queue on accounts set to semi-auto (quick approve/reject, 2 minutes)
- Records vlogs occasionally — Oybit extracts transcript, generates posts, distributes automatically
- Reviews weekly analytics summary in dashboard

**The system handles everything else** — research, generation, scoring, gating, rendering, scheduling, publishing, metrics collection, learning, persona updates.
