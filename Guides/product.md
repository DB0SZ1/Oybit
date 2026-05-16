# Oybit — Product

> A personal content intelligence system built for Ahmad. Not a SaaS. Not a tool for other people. A machine built to make one person impossible to ignore online.

---

## What Oybit Is

Oybit is Ahmad's personal autonomous content engine. It watches the internet, predicts what narratives are heating up, generates platform-native content in Ahmad's exact voice, tests it before it goes live, publishes it, measures what worked, and rewrites its own strategy from the results — with minimal human intervention.

Ahmad does not manually write posts. Ahmad does not manually schedule. Ahmad does not manually analyze. He occasionally edits `persona.md` when his direction shifts. The system handles everything else.

---

## Why This Exists

Ahmad has already proven the system works. His LinkedIn automation generated real engagement from strangers — comments, likes, 328 impressions on a single post. The problem was not whether automation works. The problem was content quality. The early posts were generic: "Working on something around X… will share later." The high-performing posts had a completely different structure:

- Real situation that happened
- System insight revealed
- Constraint or lesson
- Relatable framing
- Minimal or no CTA

Post 27: 328 impressions, 2 likes, 1 comment — modal testing case study, technical storytelling
Post 28: 383 impressions, 2 likes — GitHub library discovery, specific observation
Post 20: 5 impressions, 2 likes — Paystack key blocked, real consequence story

The pattern is clear. Oybit is built to generate that structure consistently, at scale, across 4 accounts and 3 platforms, without Ahmad having to think about it.

---

## The Scope (Exact)

**Platforms:** Instagram (personal account), Instagram (Nyvora brand account), Facebook, LinkedIn
**User count:** 1 — Ahmad only
**Goal:** 3,000–5,000 organic followers per platform by end of 2026
**Automation level:** Full auto by default. Ahmad can switch any platform to semi-auto or manual in settings
**SaaS:** No. No billing, no multi-user, no agency mode, no white-label — that comes later if the system proves itself
**Hosting:** Railway (backend + workers), Hostinger (static frontend)
**Budget:** Near-zero. Free tools only at launch

---

## The Personal Brand Angle

The thread that connects all platforms and all content:

**"Young African builder. Building real things. No permission needed."**

This is the lens every post is filtered through before it's generated. It is specific enough to be ownable, broad enough to cover everything Ahmad builds. It resonates locally (Nigeria, Africa, Abuja) and globally (indie hacker, build-in-public, developer communities).

**Per-platform projection of the same identity:**

| Account | Platform | What the algorithm rewards | Ahmad's angle | The mix |
|---|---|---|---|---|
| Personal IG | Instagram | Transformation, behind the scenes, relatability | 18yo in Abuja building real software solo, no funding | "Built a full SaaS in 3 weeks from my room" — genuine story in viral format |
| Brand IG | Instagram | Product visuals, aesthetic, authority | Nyvora as a serious tech company | Clean product shots, milestones, brand voice |
| Facebook | Facebook | Community, discussion, repurposed content | Wider reach, founder communities | Repurposed from IG and LinkedIn with slight adaptation |
| LinkedIn | LinkedIn | Lessons learned, systems thinking, founder credibility | Young African technical founder with real product portfolio | "I'm 18, I've shipped 6 products, here's what I learned" |

---

## The Winning Content Structure (Proven)

Every post Oybit generates is evaluated against this structure:

```
Real situation (something that actually happened)
    ↓
System insight (what it reveals about how something works)
    ↓
Constraint or lesson (what had to change because of it)
    ↓
Relatable framing (why someone else should care)
    ↓
Minimal CTA (optional — never forced)
```

**The Content DNA Rule:** Every post must contain at least one of:
- System insight
- Real consequence
- Technical mechanism
- Contradiction

Posts that don't pass are discarded before generation completes. This is the single rule that eliminates 60–70% of bad output.

---

## The Core Loop

```
MiroFish predicts rising narrative
→ Opportunity Detector filters through Ahmad's persona
→ Content DNA Rule applied
→ Generator produces 5–20 variants
→ Scoring AI ranks by topicality + hook strength + persona fit
→ Brand Voice Guardian hard-filters
→ Format Render Engine (text / carousel / Remotion video)
→ MiroFish Pre-Publish Gate (simulate before going live)
→ Auto-publish or approval queue (per-account setting)
→ Analytics collect saves, shares, comments, follows
→ Learning Engine updates persona.md + feeds back to MiroFish
```

This loop runs without Ahmad touching it. It improves with every post.

---

## Content Formats

| Format | Platforms | Tool | Cost |
|---|---|---|---|
| Text post | LinkedIn, Facebook | OpenRouter | Already paying |
| Carousel slides | Instagram, LinkedIn | Playwright + Jinja2 HTML | Free |
| Remotion video (clean motion graphics) | Instagram Reels, Facebook | Remotion + ffmpeg | Free |
| Image/thumbnail | All | Pollinations.ai | Free |

Video style is intentionally clean motion graphics — not filmed, not cinematic. This is the Linear/Vercel/Notion aesthetic: text animations, kinetic typography, brand colors, clean transitions. This style actually commands premium attention on Instagram and is what agencies charge thousands to produce. Oybit automates it.

---

## What Ahmad Touches

Almost nothing. The only manual intervention points:

1. **`persona.md`** — edited occasionally when direction shifts, a new product launches, or engagement patterns warrant a strategy rotation
2. **Approval queue** — only on accounts set to semi-auto mode
3. **Manual vlogs** — when Ahmad records something, the content engine extracts the transcript, generates platform-native posts from it, and distributes automatically

Everything else is the system.

---

## The North Star

By end of 2026: 3–5k organic followers on each of the 4 accounts.
By the time Oybit opens to other users: Ahmad's own growth numbers are the sales page.
The product proves itself on the founder before it asks anyone else to trust it.
