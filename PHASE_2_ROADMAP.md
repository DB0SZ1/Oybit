# Phase 2 Roadmap: Features & Modules

The following features were defined in the system architecture specification but deferred from the Phase 1 launch. They require dedicated infrastructure builds.

## 1. Meme Video Module
- **Description:** Generates dev humor short-form video posts by combining a pre-sourced video clip with an AI-generated caption overlay baked directly into the video.
- **Dependencies:** `ffmpeg-python`
- **Implementation Strategy:** 
  1. Create a `data/meme_seeds/` directory to store 5 raw MP4 seed videos.
  2. Build `backend/render_engine/meme_video.py` using `ffmpeg` to overlay the OpenRouter-generated text onto the raw MP4 clips.
  3. Wire into `opportunity_worker.py` format selection (`reel`).

## 2. Community & Forum Module (Reddit & FB Groups)
- **Description:** Campaign-driven behavior that joins subreddits/groups, monitors threads, and drafts genuinely helpful responses that occasionally mention ColdSift/C0DE.
- **Dependencies:** `praw` (Reddit API wrapper), Facebook Graph API extensions.
- **Implementation Strategy:**
  1. Build `reddit_worker.py` to crawl target subreddits for keywords/problems.
  2. Route inbound problems through MiroFish to evaluate if they match a Campaign brief.
  3. Draft and queue responses for operator approval.

## 3. Campaign Mode
- **Description:** A focused, time-bound activation targeting a specific goal or product, separate from the regular daily posting schedule.
- **Implementation Strategy:**
  1. Create `Campaign` database model (target product, goal, subreddits, tone rules).
  2. Update MiroFish narrative generation to prioritize active campaign briefs over generic trends.

## 4. Strict Content Ratios
- **Description:** Enforce exact ratios (e.g., exactly 3 Memes and 2 Carousels per 5 posts) rather than random weighted chances.
- **Implementation Strategy:**
  1. Add `post_cycle_count` tracking to the database per account.
  2. Update `opportunity_worker.py` to strictly rotate through the 5-post cycle.

## 5. Long-Form Video (Remotion)
- **Description:** Fully automated programmatic videos via Remotion.
- **Status:** Deferred until the premium Remotion template is built externally and imported into `backend/render_engine/templates/video/`.
