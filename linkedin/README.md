---
title: Oybit Linkedin
emoji: 🦀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---
# Oybit LinkedIn Bot 🦀

This is the backend service for the **Oybit LinkedIn Bot**, a fully autonomous content generation and publishing engine. It orchestrates drafting content, selecting/generating media, evaluating it against a simulated audience (MiroFish), and publishing directly to LinkedIn.

## 🌟 Current Status & Features

As of **June 2026**, the following features are actively implemented and functional:

### 1. Content Generation Pipeline (`api_routes/content.py`)
- **LLM Integration**: Uses OpenRouter to draft LinkedIn posts (threads, short-form, etc.) based on defined personas and topic pillars.
- **Scoring System**: Automatically scores the generated draft across three metrics: Hook, Persona, and Topicality.

### 2. Media Engine
- **Media Library Selector (`services/media_selector.py`)**: Automatically scans `data/media_library/` and uses `tags.json` to intelligently match existing images/media to the specific topic pillar of the post.
- **Playwright Carousel Fallback (`render_engine/carousel.py`)**: If no matching image is found in the media library, the bot uses Playwright to launch a headless Chromium browser, chunks the post text into slides, and renders a sleek, styled HTML carousel of screenshots automatically.
- **Static File Serving**: Serves the generated media URLs (from `data/media_library` and `data/tmp`) over FastAPI so the Frontend Dashboard can preview them securely.

### 3. Audience Simulation (MiroFish)
- **Gatekeeping**: Before a post goes live, it is sent to the `MiroFish` engine which simulates audience backlash or engagement.
- If the post's confidence score drops too low, it is held in a `draft` state for revision.

### 4. Publishing Engine (`publishers/linkedin.py`)
- If the post passes the MiroFish gate, it connects to the LinkedIn API v2 (UGC Posts).
- **Media Uploads**: Seamlessly uploads the selected image or Playwright carousel slides to LinkedIn's asset storage before attaching them to the published post.

## 📂 Directory Structure
- `/api_routes`: FastAPI routers handling the pipeline, simulation, and endpoints (like `GET /posts` for UI previews).
- `/data`: Local storage for the `media_library` and `tmp` processing folders.
- `/db`: SQLAlchemy models and SQLite connection handling.
- `/publishers`: Platform-specific API logic (LinkedIn UGC).
- `/render_engine`: Houses the Playwright HTML-to-Image carousel generator.
- `/scripts`: Automation and testing scripts (e.g., `test_pipeline.py`).
- `/services`: Helper services like LLM calling and Media Library selection.

## 🚀 How to Run
Use the global `start_test_env.bat` in the root Oybit folder to launch this backend (Port `8005`) alongside the Next.js Dashboard.

## 🔄 Upcoming / TODO
- Refine the HTML/CSS template for the Playwright carousel slides.
- Integrate the LinkedIn video publishing pipeline.
- Expand the frontend UI to include detailed analytics tracking for these published posts.
