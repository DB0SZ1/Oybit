# OYBIT PLATFORM — SYSTEM ARCHITECTURE MAP
## (LLM Context Document)

---

## OVERVIEW

The **Oybit Platform** is an AI-powered brand content pipeline that:
1. Ingests a brand's identity and persona
2. Detects content opportunities
3. Generates, scores, simulates, and quality-gates content
4. Renders and publishes content to the right platforms
5. Collects analytics and feeds them back into a learning loop

The platform has **one primary AI brain** called **Mirofish Intelligence**, which appears at multiple stages in different roles (narrative simulation, pre-publish gating, and overall intelligence coordination).

---

## COMPONENTS (in execution order)

### 1. USER-BRAND PERSONA
- **What it is:** The entry point of the system.
- **Role:** Defines who the brand is — tone, values, audience, identity, voice style.
- **Input:** Human-configured brand profile.
- **Output:** Brand context fed into Mirofish Intelligence.
- **Analogy:** Like a creative brief given to an agency before any work starts.

---

### 2. MIROFISH INTELLIGENCE
- **What it is:** The core AI engine of the platform. Acts as the "brain."
- **Role:** Processes the brand persona and orchestrates downstream components.
- **Input:** User-brand persona data.
- **Output:** Directives to the Opportunity Detection layer.
- **Special note:** Mirofish Intelligence also receives the **feedback loop** from the Learning Engine at the end of the pipeline — meaning it continuously improves over time as the platform learns what content performs well for each brand.
- **Analogy:** Like a senior creative strategist who knows the brand deeply and directs the team.

---

### 3. OPPORTUNITY DETECTION
- **What it is:** An AI scanning layer.
- **Role:** Identifies content opportunities — trending topics, platform moments, audience gaps, seasonal hooks.
- **Input:** Brand context from Mirofish Intelligence.
- **Output:** Detected opportunities passed to the Content Generation Engine.
- **Analogy:** Like a social listening + trend analysis tool that flags "now is a good time to post about X."

---

### 4. CONTENT GENERATION ENGINE
- **What it is:** The content creation layer.
- **Role:** Generates raw content drafts based on detected opportunities and brand persona.
- **Input:** Opportunity signals.
- **Output:** Draft content passed to Mirofish Narrative Simulation.
- **Analogy:** Like a copywriter generating first drafts.

---

### 5. MIROFISH NARRATIVE SIMULATION
- **What it is:** A simulation sub-module of Mirofish Intelligence.
- **Role:** Simulates how the generated content will perform narratively — tests coherence, brand alignment, emotional resonance, and audience fit before scoring.
- **Input:** Raw content drafts from the Content Generation Engine.
- **Output:** Simulated content passed to Multi-Scoring AI.
- **Analogy:** Like a focus group simulation or a "what will people think when they read this?" test run by AI.

---

### 6. MULTI-SCORING AI
- **What it is:** A multi-dimensional content evaluation layer.
- **Role:** Scores content across multiple axes (quality, brand fit, engagement potential, platform suitability, etc.).
- **Input:** Narrative-simulated content.
- **Output (primary):** Scored content passed to the Format Render Engine.
- **Output (secondary):** Sends content to **Brand Voice** checker (side component).
- **Analogy:** Like an editorial review board that grades content before it moves forward.

---

### 6a. BRAND VOICE (Side Component)
- **What it is:** A brand consistency checker, triggered by Multi-Scoring AI.
- **Role:** Verifies that the content sounds like the brand — matches the tone, vocabulary, and personality defined in the User-Brand Persona.
- **Input:** Content from Multi-Scoring AI.
- **Output:** Approval/flag back to the scoring process.
- **Relationship:** Sits to the LEFT of Multi-Scoring AI. Arrow points FROM Multi-Scoring AI TO Brand Voice (i.e., Multi-Scoring AI sends content here for a voice check).
- **Analogy:** Like a brand guardian or tone-of-voice editor.

---

### 7. FORMAT RENDER ENGINE
- **What it is:** The content formatting layer.
- **Role:** Takes scored content and renders it into the correct format — captions, blog posts, video scripts, carousels, etc.
- **Input:** Approved scored content from Multi-Scoring AI.
- **Output (primary):** Formatted content to Platform Adapter Layer.
- **Output (secondary):** Sends formatted content to **Mirofish Pre-Publish Gate** for final quality check.
- **Analogy:** Like a designer/formatter who turns a brief into a finished asset.

---

### 7a. MIROFISH PRE-PUBLISH GATE (Side Component)
- **What it is:** A final quality gate, another Mirofish sub-module.
- **Role:** Performs a last AI-driven check on the formatted content before it is published — checks for errors, brand safety, platform compliance, and quality standards.
- **Input:** Formatted content from Format Render Engine.
- **Output:** Approval to proceed to publishing, or rejection back for revision.
- **Relationship:** Sits to the RIGHT of the Format Render Engine. Arrow points FROM Format Render Engine TO Pre-Publish Gate.
- **Analogy:** Like a final editorial sign-off or a legal/compliance review before going live.

---

### 8. PLATFORM ADAPTER LAYER
- **What it is:** A platform-specific adaptation layer.
- **Role:** Adapts the formatted, approved content for the specific requirements of each target platform (Instagram, LinkedIn, X/Twitter, TikTok, newsletters, etc.) — sizing, character limits, hashtag strategies, etc.
- **Input:** Approved formatted content.
- **Output:** Platform-ready content to Publishing System.
- **Analogy:** Like a platform specialist who knows the rules and best practices for each channel.

---

### 9. PUBLISHING SYSTEM
- **What it is:** The distribution layer.
- **Role:** Pushes content live to the appropriate platforms at the right time.
- **Input:** Platform-adapted content.
- **Output:** Published content + triggers Analytics Collector.
- **Analogy:** Like a social media scheduler (Buffer, Hootsuite) but integrated into the pipeline.

---

### 10. ANALYTICS COLLECTOR
- **What it is:** The performance data ingestion layer.
- **Role:** Gathers post-publish performance data — engagement rates, reach, clicks, sentiment, conversion signals.
- **Input:** Published content performance data from platforms.
- **Output:** Performance data to Learning Engine.
- **Analogy:** Like a built-in analytics dashboard that captures what worked and what didn't.

---

### 11. LEARNING ENGINE
- **What it is:** The intelligence improvement layer.
- **Role:** Processes analytics data and extracts learnings — what content formats, topics, tones, and timings perform best for this specific brand.
- **Input:** Analytics data from Analytics Collector.
- **Output (primary):** Learnings stored in **Memory System**.
- **Output (secondary):** Feeds updated intelligence BACK to **Mirofish Intelligence** (this is the main feedback loop — shown as a dashed line going back to the top of the diagram).
- **Analogy:** Like a performance review meeting where the team updates their strategy based on results.

---

### 12. MEMORY SYSTEM
- **What it is:** The persistent knowledge store.
- **Role:** Stores all accumulated learnings about the brand — what worked, brand evolution, audience response history, successful content patterns.
- **Input:** Learnings from the Learning Engine.
- **Output:** Referenced by Mirofish Intelligence and other components to improve future content cycles.
- **Relationship:** Sits to the BOTTOM RIGHT of the diagram. Connected to the Learning Engine by a diagonal arrow.
- **Analogy:** Like a brand's institutional memory or a fine-tuned model that knows this brand better than any generic AI.

---

## FEEDBACK LOOPS

### Primary Feedback Loop (Dashed right-side bracket)
- **Path:** Analytics Collector → Learning Engine → Mirofish Intelligence
- **Purpose:** The platform continuously improves. Every piece of published content teaches the system what works for this brand.
- **Visual:** Shown as a dashed bracket on the RIGHT side of the diagram labeled "Feedback loop."

### Simulation Learning Loop (Dashed left-side bracket)
- **Path:** Format Render Engine → Platform Adapter Layer → Publishing System (the lower half of the pipeline)
- **Purpose:** This section is specifically part of the "simulation learning" process — the platform learns from how content moves through formatting and publishing stages.
- **Visual:** Shown as a dashed bracket on the LEFT side labeled "Simulation learning."

---

## DATA FLOW SUMMARY (Linear Path)

```
User-Brand Persona
        ↓
Mirofish Intelligence ←─────────────────────────────────(Feedback Loop)
        ↓
Opportunity Detection
        ↓
Content Generation Engine
        ↓
Mirofish Narrative Simulation
        ↓
Multi-Scoring AI ──→ Brand Voice (side check)
        ↓
Format Render Engine ──→ Mirofish Pre-Publish Gate (side check)
        ↓
Platform Adapter Layer
        ↓
Publishing System
        ↓
Analytics Collector
        ↓
Learning Engine ──→ Memory System
        ↓
(feeds back to Mirofish Intelligence)
```

---

## KEY DESIGN PRINCIPLES OF THIS SYSTEM

1. **Brand-first:** Every component is anchored to the brand persona. The system does not generate generic content — it generates brand-specific content.
2. **Multi-gate quality control:** Content passes through THREE quality checks before publishing — Narrative Simulation, Multi-Scoring AI + Brand Voice, and Pre-Publish Gate.
3. **Self-improving:** The Memory System + Learning Engine + Feedback Loop means the platform gets smarter with every content cycle for every brand.
4. **Mirofish is the intelligence layer:** Mirofish is not a single box — it is a distributed intelligence that appears in three roles: (a) core orchestration, (b) narrative simulation, and (c) pre-publish gating.
5. **Platform-agnostic output:** The Platform Adapter Layer means content can be published anywhere without the upstream pipeline needing to change.

---

## GLOSSARY

| Term | Meaning |
|---|---|
| Mirofish Intelligence | The platform's core AI engine; orchestrates the whole pipeline |
| Brand Voice | The consistent tone, language, and personality of a brand |
| Narrative Simulation | AI-driven prediction of how content will land with an audience |
| Multi-Scoring AI | Scores content on multiple quality and brand dimensions |
| Pre-Publish Gate | Final AI quality check before content goes live |
| Platform Adapter | Reformats content to meet each platform's specific requirements |
| Memory System | Persistent store of brand-specific learnings |
| Learning Engine | Extracts insights from analytics to improve future content |
| Opportunity Detection | Scans for timely, relevant content moments for the brand |

---

*Document generated from hand-drawn architecture diagram. Oybit Platform — mental model.*