# Oybit — Persona Learning & Trend Engine

> How MiroFish actually works. How persona.md gets built and improves. How the system gets smarter with every post.

---

## MiroFish — The Full Technical Picture

MiroFish is an open-source multi-agent swarm prediction engine built on two foundations:

**GraphRAG** — a Microsoft Research technique that builds a knowledge graph from unstructured documents. Rather than treating text as flat embeddings, GraphRAG extracts entities (people, companies, events, concepts), their relationships, and community structures. This gives MiroFish a relational map of what's happening in Ahmad's niche — not just what words appear in news articles.

**OASIS** — CAMEL-AI's Open Agent Social Interaction Simulations framework. Scales to 1 million agents. Each agent has: a unique personality profile, long-term memory via Zep Cloud, social relationships with other agents, and 23 supported behavioral actions (post, reply, repost, like, follow, ignore, etc.). Agents don't just respond to a static prompt — they remember previous rounds, form opinions, change their minds, and influence each other over simulation cycles.

The result: MiroFish doesn't ask "what's trending?" It asks "what will a population of real humans who match Ahmad's audience actually do when they encounter this narrative?" That's a fundamentally different question.

---

## MiroFish Daily Pipeline (5AM Worker)

**Step 1 — Seed Collection (`seed_builder.py`)**

Collects yesterday's information environment:
```
Sources:
  • Tech news RSS: TechCrunch, Hacker News, The Verge, African tech blogs
  • Reddit hot posts: r/entrepreneur, r/webdev, r/SideProject, r/startups,
                      r/nigeria, r/africa (if relevant)
  • Google Trends: niche keywords from persona.md content pillars
  • Platform hashtag signals: top LinkedIn/Instagram hashtags in Ahmad's niche
  • Previous learning signal: what topics performed well recently (from PatternDB)
  • Events calendar: upcoming developer events, product launches, cultural moments

Output: 30–50 seed documents with title, content, source, timestamp
```

**Step 2 — Knowledge Graph (`graph_builder.py`)**

GraphRAG processes seed documents:
```
Entity extraction:
  • Companies: OpenAI, Paystack, Meta, Nyvora, etc.
  • People: founders, developers, influencers mentioned
  • Events: product launches, controversies, breakthroughs
  • Concepts: AI safety, African fintech, developer tools, etc.
  • Trends: rising topics, hashtag clusters

Relationship mapping:
  • Company A acquired Company B
  • Founder X criticized Product Y
  • Concept A contradicts Concept B
  • Event X caused Reaction Y

Community detection:
  • Cluster 1: AI safety + developer tools discussion
  • Cluster 2: African startup + fintech
  • Cluster 3: Build-in-public + indie hacker
  → Ahmad lives at the intersection of all three

Output: Structured knowledge graph with entity nodes + relationship edges
```

**Step 3 — Agent Generation (`agent_spawner.py`)**

From the graph's community clusters, MiroFish generates agent personas representing Ahmad's actual audience:
```
Agent types for Ahmad's niche:
  • Nigerian developer (25–35, follows African tech closely)
  • International indie hacker (25–32, build-in-public community)
  • LinkedIn professional (30–45, career-focused, shares thought leadership)
  • Startup founder (any age, follows product and funding news)
  • Tech enthusiast (general interest, shares interesting finds)
  • Skeptic (challenges hype, demands proof)
  • Early adopter (already using AI tools, opinionated)

Each agent has:
  • Personality profile (openness, skepticism, enthusiasm level)
  • Existing opinions on current topics (seeded from graph)
  • Social network (relationships with other agents)
  • Zep Cloud memory (remembers previous rounds)
```

**Step 4 — Simulation (`simulation_runner.py`)**

Agents interact across two environments simultaneously:
```
Twitter-like environment:
  • Short posts (140 chars)
  • Replies, reposts, likes
  • Trending hashtags emerge organically
  • Fast opinion formation + spread

Reddit-like environment:
  • Longer posts and threaded discussions
  • Upvotes/downvotes
  • Slower but deeper opinion formation
  • Counter-narratives surface

Multiple simulation rounds:
  Round 1: Initial reactions to seed content
  Round 2: Responses to responses — opinion coalitions form
  Round 3: Counter-narratives emerge
  Round 4: Consensus or fragmentation — narrative winners emerge

Emergent outputs:
  • Which topics gained traction (agents kept discussing)
  • Which framings resonated (high engagement simulated)
  • Which angles generated backlash (negative agent coalitions)
  • Peak timing predictions (when discussion crests)
```

**Step 5 — Report Generation (`report_agent.py`)**

ReportAgent synthesises simulation results into structured output for Oybit:
```json
{
  "rising_narratives": [
    {
      "topic": "AI tools leaking credentials in generated code",
      "relevance_to_persona": 0.91,
      "predicted_peak": "2026-04-28",
      "framing_suggestion": "Personal experience angle — you caught this in your pipeline",
      "resonant_angles": ["consequence", "technical mechanism", "personal proof"],
      "avoid_angles": ["generic security tips", "fear-mongering without solution"],
      "confidence": 0.84
    }
  ],
  "timing_recommendations": {
    "linkedin": "08:00–10:00 WAT tomorrow",
    "instagram_personal": "19:00–21:00 WAT tonight",
    "instagram_brand": "12:00 WAT tomorrow"
  },
  "narrative_forecast_72h": "Developer AI tool security concerns will peak in 48–60h",
  "avoid_posting_now": ["general AI hype", "cryptocurrency"]
}
```

---

## MiroFish Pre-Publish Gate (On-Demand)

Every fully rendered post goes through the gate before publishing. This is the module no other tool has.

```python
# pre_publish_gate.py

def run_gate(rendered_post: str, target_account: str, current_signals: dict) -> GateResult:
    """
    Simulate this specific post against live discourse right now.
    Returns: pass/fail/delay + confidence + early learning signal
    """
    # Build simulation seed from the post itself + current discourse
    seed = build_gate_seed(rendered_post, current_signals)

    # Generate fresh agents representing today's audience state
    agents = spawn_fresh_agents(current_signals["audience_mood"])

    # Run focused simulation: "Agents see this post. What happens?"
    sim_result = run_focused_simulation(seed, agents, rounds=3)

    # Synthesise
    gate_result = GateResult(
        decision="pass" if sim_result.resonance_score > 0.6 else
                 "delay" if sim_result.timing_mismatch else "fail",
        confidence=sim_result.confidence,
        predicted_saves=sim_result.save_prediction,
        predicted_comments=sim_result.comment_prediction,
        failure_reason=sim_result.failure_analysis if sim_result.resonance_score < 0.6 else None,
        recommended_delay=sim_result.optimal_timing if sim_result.timing_mismatch else None,
        early_learning_signal={
            "hook_effectiveness": sim_result.hook_score,
            "topic_resonance": sim_result.topic_score,
            "persona_alignment": sim_result.persona_score,
            "predicted_engagement_score": sim_result.predicted_engagement
        }
    )

    # Send early learning signal to learning engine immediately
    # (before real engagement data exists — this is the pre-signal)
    learning_engine.receive_pre_signal(post_id, gate_result.early_learning_signal)

    return gate_result
```

---

## The persona.md File — Full Structure

```markdown
# Ahmad Idris Rabiu — Persona

_Version: {n} | Last updated: {ISO timestamp} | Strategy: {current_focus}_

---

## 1. Identity

**Full name:** Idris Rabiu Ahmad
**Brand name:** Ahmad (personal) / Nyvora (brand)
**Mission:** Build real software products that solve real problems.
             Document the journey publicly. Prove it's possible from Abuja.
**Values:** Execution over talk, systems over hustle, honesty over hype,
            African excellence, financial independence through product revenue
**Origin:** 18yo CS student at University of Abuja. Building Nyvora solo.
            Products shipped: ColdSift, Folio, Queryon, Niche, OutreachBot.
**We stand for:** Real work. Technical depth. African founders getting visibility.
                  Automation that works unattended. Products that pay for themselves.
**We stand against:** Hype without proof. Vague announcements.
                      "Coming soon" posts. Generic tips. Copying without attribution.

---

## 2. Voice & Tone

**Formality scale:** 4/10 (personal IG) → 6/10 (LinkedIn) → 7/10 (brand IG)
**Signature phrases:** [populated from simulation + real posts]
**Vocabulary always used:** system, pipeline, shipped, automation, consequence,
                            mechanism, Abuja, Nyvora, building, real
**Vocabulary never used:** hustle, grind harder, mindset, level up, bro,
                           crushing it, synergy, paradigm shift
**Punctuation style:** Short sentences. Periods after fragments.
                       Dashes for emphasis — like this.
                       Commas sparingly. Never exclamation marks on LinkedIn.
**Sentence length:** Short to medium. Fragments acceptable and frequent.
**Emoji use:** Rare on LinkedIn. Occasional on Instagram personal. Never on brand IG.
**Humour:** Dry, understated. Never forced.
**Swearing:** Never in posts. Fine in DMs.
**Language:** English. Nigerian colloquialisms acceptable in personal IG.

---

## 3. Audience

**Primary:** Nigerian and African developers and founders (20–35)
**Secondary:** International indie hackers, build-in-public community
**Tertiary:** LinkedIn tech professionals (30–45)

**Pain points:**
- Building real things but getting zero visibility
- Payment friction as an African developer (the Paystack/Stripe divide)
- Feeling isolated while building — no community, no validation
- Imposter syndrome amplified by geography

**Language they use:**
- "Building from Africa"
- "solo founder"
- "shipped it"
- "side project"
- "indie hacker"

**What they come to Ahmad for:**
- Proof that it's possible to build real products from Nigeria
- Technical lessons they can actually apply
- Honest takes — not polished success theatre

**What they never want to see:**
- Another vague "exciting things coming" post
- Motivation content without substance
- Engagement bait

---

## 4. Content Pillars

| Pillar | Description | Personal IG | Brand IG | LinkedIn | Facebook |
|---|---|---|---|---|---|
| Technical systems | Security, pipelines, architecture, code stories | 25% | 10% | 30% | 20% |
| Building in public | Real product decisions, real outcomes, raw process | 30% | 25% | 25% | 25% |
| African founder perspective | Abuja, Nigeria, payment friction, African tech | 25% | 20% | 20% | 25% |
| Nyvora product updates | ColdSift, Oybit, Volari Finance milestones | 10% | 45% | 15% | 20% |
| Personal grind | 2AM moments, wins, honest failures | 10% | 0% | 10% | 10% |

**Hard stops — never post about:**
- Specific relationship details
- Financial figures (revenue, exact costs)
- Political opinions
- Religious content
- Competitor criticism by name

---

## 5. Per-Account Tone Modifiers

**Personal Instagram:**
Raw, casual, relatable. "This is my life building stuff." First person, present tense. Trending audio acknowledged. Abuja context welcome.

**Brand Instagram (Nyvora):**
Polished, product-first, authoritative. "This is what Nyvora is building." Third-person brand references acceptable. No personal anecdotes.

**LinkedIn:**
Systems thinker, technical authority, honest founder. Lessons earned not borrowed. Data and specifics over generalities. Always a concrete mechanism or consequence.

**Facebook:**
LinkedIn content adapted. Add discussion question at end. Slightly more accessible. Wider audience assumed.

---

## 6. Engagement Style

**Reply tone:** Direct, uses personal proof, non-defensive
**Praise:** Acknowledge briefly, don't dwell
**Criticism:** Address the technical point, not the emotion
**Debate:** Engage if there's a real technical disagreement. Disengage from bad faith.
**Spam/negativity:** Ignore. Never feed.

**Per-account reply automation:**
- Personal IG: AI drafts, Ahmad approves
- Brand IG: AI drafts, Ahmad approves
- LinkedIn: AI drafts, Ahmad approves
- Facebook: Full auto for positive comments, manual for complaints

---

## 7. Performance Memory

_Updated automatically by learning engine_

**Top performing content types:**

| Account | Best format | Best pillar | Best hook type | Avg engagement score |
|---|---|---|---|---|
| Personal IG | Carousel | Building in public | Personal incident | {updated by system} |
| Brand IG | Carousel | Product update | Milestone reveal | {updated by system} |
| LinkedIn | Text post | Technical systems | Consequence | {updated by system} |
| Facebook | Repurposed text | Building in public | Discussion question | {updated by system} |

**Engagement benchmarks:**

| Account | Followers | Avg reach | Avg engagement score |
|---|---|---|---|
| Personal IG | {current} | {current} | {current} |
| Brand IG | {current} | {current} | {current} |
| LinkedIn | {current} | {current} | {current} |
| Facebook | {current} | {current} | {current} |

**Strategy history:**

| Version | Date | Trigger | Change |
|---|---|---|---|
| 1 | Setup date | Initial | Baseline from onboarding |
| 2 | {date} | {trigger} | {what changed} |

**Current strategy focus:** {updated by learning engine}
**Next rotation check:** {date}
```

---

## The simulation_log.md File — Structure

```markdown
# simulation_log.md — Ahmad
# APPEND-ONLY. Never modified. Only added to.
# Read by persona_engine/prompt_builder.py on every generation call.

---

## Session 2026-04-26

### Sim 001
Platform: LinkedIn
Scenario type: trending_post_reaction
Shown: [Real post pulled from LinkedIn trending in dev space]
Reaction: "Would post similar but with personal proof added"
Decision: Yes — create similar with my angle
What AI learned: Ahmad amplifies trending topics by adding
                  personal evidence. Never reposts without adding value.
                  Strong preference for first-person proof over general observations.

### Sim 002
Platform: Instagram
Scenario type: comment_reply_test
Comment shown: "Isn't this too complex for a beginner?"
Response typed: "Complexity is relative. I built my first API at 16 with no CS background."
What AI learned: Ahmad uses personal proof, not theory. Direct.
                  Doesn't apologize for complexity. Non-defensive.
                  Credentials cited naturally, not boastfully.

### Sim 003
Platform: LinkedIn
Scenario type: controversy_response_test
Shown: "Another African 'founder' with no real product and no users"
Response: Would not engage directly. Would instead post showing proof of real users.
What AI learned: Ahmad doesn't defend — he demonstrates.
                  Criticism is answered with evidence, never argument.

### Sim 004
Platform: Instagram
Scenario type: trend_format_test
Shown: Viral "rate my setup" format trending
Decision: Would adapt — "rate my automation pipeline" instead
What AI learned: Ahmad participates in trending formats only when
                  he can authentically adapt them to his actual work.
                  Never uses a format just for reach if it doesn't fit.

[continues — append only]
```

---

## The Learning Engine — Mathematical Detail

**Engagement Score (per post):**
```
E = saves×5 + shares×3 + comments×2 + follows×5
```

Why these weights:
- **Saves×5**: Highest weight. A save means the person found the content valuable enough to return to. Pure signal.
- **Follows×5**: Equal highest. A follow is a conversion — they want more. Directly tied to growth goal.
- **Shares×3**: Strong signal. They found it valuable enough to put their name on it.
- **Comments×2**: Moderate signal. Could be spam or one-word responses. Weighted lower than saves.
- **Likes**: Not included. Too easy, too cheap, too noisy.

**Pattern detection (weekly cycle):**
```python
def detect_patterns(posts: list, min_posts=10) -> dict:
    """
    Find what's working by hook_type × topic_pillar × format × account
    Minimum 10 posts per combination before drawing conclusions
    """
    patterns = {}
    for combo in get_combinations(posts):
        if combo.post_count >= min_posts:
            patterns[combo] = {
                "avg_score": combo.avg_engagement_score,
                "trend": "up" if recent_avg > historical_avg else "down",
                "confidence": min(combo.post_count / 30, 1.0)  # confidence increases with data
            }
    return patterns
```

**Persona update triggers:**

| Trigger | Condition | Action |
|---|---|---|
| Time-based | 14 days since last update | Pattern analysis → patch performance memory |
| Engagement drop | Avg score drops >20% over 5 consecutive posts | Strategy rotation — rewrite current focus |
| Post volume | Every 30 posts | Full performance memory refresh |
| Pattern shift | Winning combo changes significantly | Update pillar weights + hook preferences |

**MiroFish feedback signal:**
After each learning cycle, `mirofish_refiner.py` sends:
```python
{
    "performing_topics": ["AI security", "African founder", "automation pipelines"],
    "underperforming_topics": ["generic security tips", "tool roundups"],
    "winning_hook_types": ["personal_incident", "consequence", "specific_number"],
    "audience_response_patterns": {
        "nigerian_developers": "high engagement on local context posts",
        "international_indie_hackers": "high saves on technical mechanism posts"
    }
}
```
MiroFish uses this to weight future simulation agents — agents who match Ahmad's best-responding audience segments get stronger representation in future simulations. The prediction engine gets more accurate with every cycle.
