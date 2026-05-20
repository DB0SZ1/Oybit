---
title: Oybit
emoji: 🚀
colorFrom: red
colorTo: red
sdk: docker
pinned: false
---

# Oybit: Autonomous Content Swarm & Rendering Engine

**Oybit** is a production-grade, unsupervised content generation and rendering engine designed to operate as an autonomous "ghostwriter" and digital designer for founders, agencies, and brands. 

Rather than relying on basic LLM prompts, Oybit operates via a sophisticated **Swarm Intelligence** architecture. It proactively detects internet trends, debates internal narratives, strictly enforces brand guidelines, and natively designs its own high-fidelity graphics (JPEGs, PDFs) before autonomously publishing them across major social platforms.

---

## 🚀 Core Capabilities

### 1. Autonomous Trend Aggregation
Oybit does not wait to be told what to write about. It runs 24/7 background daemons that actively scrape and monitor:
*   **RSS Feeds:** (TechCrunch, HackerNews, etc.)
*   **Google Trends:** Live interest data on specific tech, SaaS, and startup keywords.
*   **MiroFish Simulation:** Extracts deep, opinionated narratives from the aggregated noise.

### 2. Multi-Agent "Writer's Room" (MiroFish)
Instead of a single AI prompt, Oybit spins up a 20-agent simulation. The agents debate the current trends, extract contrarian opinions, and formulate highly engaging narratives. This ensures the output is intellectually sharp, nuanced, and devoid of generic "AI slop."

### 3. The Persona Guardian
Every generated post must pass through the Guardian node, which acts as an iron-clad brand filter. It cross-references the content against a strict `master_strategy_doc.md` and `persona.md`. 
*   If the AI uses corporate jargon, engagement bait (e.g., "like and share"), or starts a LinkedIn post with "I", the Guardian rejects it and forces a rewrite. 
*   It ensures distinct platform tones: Raw and relatable for Instagram, highly technical for LinkedIn, and community-focused for Facebook.

### 4. Headless Playwright Render Engine
Oybit does not just output text—it acts as an autonomous graphic designer. It uses a headless Chromium/Edge browser to render code-based HTML/CSS/Jinja2 templates into stunning visual assets.
*   **High-Fidelity Carousels:** Generates 5–10 slide sequences.
*   **Dynamic Scrapbook Art:** Automatically injects randomized SVG doodles, hand-drawn circle annotations, and 3D Lottie animations into the slides.
*   **Trending Hot Takes:** Automatically downloads the high-res hero image (`og:image`) from a scraped news article and uses it as a full-bleed cinematic background for opinion posts.
*   **LinkedIn Native PDFs:** Automatically stitches generated JPEG slides into a single, high-quality PDF document optimized for LinkedIn's carousel algorithm.

### 5. Automated Distribution & Growth
Once content is written, guarded, and rendered, the Dispatcher node publishes it.
*   **Supported Platforms:** LinkedIn (PDF/Text), Instagram (Personal & Brand), Facebook.
*   **Format Selection:** Intelligently rotates formats (Text, Images, Carousels) based on strict campaign ratios to maximize feed variety.
*   **Autonomous Following:** Engages in targeted follow-strategies to organically grow the account's footprint.

---

## ⚙️ How It Works (The Pipeline)

When the `opportunity_worker` detects a content gap, the pipeline executes in this exact sequence:

1. **Trend Ingestion:** Pulls the hottest narrative from the MiroFish swarm.
2. **Generation:** Drafts the post copy and slide text based on the brand's exact tone.
3. **Scoring & Gating:** The Guardian node scores the content against brand rules. It must score >85% or it is rewritten.
4. **Visual Rendering:** The slide text is pushed into the Jinja2 template matrix. Playwright boots up, applies the CSS styling and SVG assets, and snaps the assets (JPEGs or PDF).
5. **Pre-Publish Verification:** Ensures all visual assets rendered correctly and are within platform file limits.
6. **Publishing:** Dispatches via Meta Graph API and LinkedIn API.

---

## 🧠 Integrated Services & Ecosystem

Oybit orchestrates multiple services into a single autonomous pipeline:
*   **OpenRouter:** Powers the core LLM logic (Llama-3 / Claude 3.5 Sonnet) for writing and Guardian scoring.
*   **Zep API:** Provides long-term vector memory for the MiroFish agent swarm, allowing them to remember past narratives and avoid repeating topics.
*   **Playwright Engine:** The local headless browser powering the visual rendering.
*   **Pollinations API:** Fallback API for generating abstract minimal thumbnail images when template rendering is bypassed.
*   **SQLite / SQLAlchemy:** Manages the internal state, tracking post cycles, worker heartbeats, and trend signals.

*Oybit is a closed-source infrastructure system developed by Nyvora / C0DE.*
