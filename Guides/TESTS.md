# TESTS.md — Oybit Test Scripts Manifest

> Every module gets a test script. No module is considered built until its test passes.
> Tests are standalone scripts — not pytest, not unittest. Just `python scripts/test_<module>.py` and it either works or it doesn't.
> Run your tests before moving to the next phase. A passing test is your sign-off.

---

## Rules

1. Every test script prints clear PASS / FAIL for each check
2. Tests use real data where possible — fake data only when APIs would cost money or require live accounts
3. Tests are in `/scripts/tests/` — one file per module
4. Each test is runnable independently: `python scripts/tests/test_<module>.py`
5. Tests do NOT modify production data — use test_ prefixed records in DB, clean up after
6. If a test fails, the agent fixes the module before moving on. No skipping.

---

## Test Script Template

Every test file follows this structure:

```python
# scripts/tests/test_<module_name>.py
# Run: python scripts/tests/test_<module_name>.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def check(label: str, condition: bool, detail: str = ""):
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"  {status} — {label}")
    if not condition and detail:
        print(f"         Detail: {detail}")
    return condition

def run():
    print(f"\n{'='*50}")
    print(f"TEST: <module_name>")
    print(f"{'='*50}")
    results = []

    # --- your checks here ---
    # results.append(check("Description of check", some_condition, "optional detail on failure"))

    passed = sum(results)
    total = len(results)
    print(f"\n  Result: {passed}/{total} checks passed")
    print(f"{'='*50}\n")
    return passed == total

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
```

---

---

# AGENT A — Test Scripts to Build

---

## `scripts/tests/test_content_dna_checker.py`

**Tests:** `backend/intelligence/content_dna_checker.py`

```
Checks:
1. Post with clear system insight → has_system_insight=True, passes=True
2. Post with real consequence → has_real_consequence=True, passes=True
3. Post with technical mechanism → has_technical_mechanism=True, passes=True
4. Post with contradiction → has_contradiction=True, passes=True
5. Post with multiple DNA elements → all relevant fields True, passes=True
6. Generic post ("Working on something exciting, will share soon") → ALL fields False, passes=False
7. Generic motivational post ("Keep going, success is near") → passes=False
8. Vague announcement post ("Big news coming") → passes=False
9. Return type is DNAResult with correct fields (has_system_insight, has_real_consequence, has_technical_mechanism, has_contradiction, passes)
10. Function handles empty string input without crashing
```

---

## `scripts/tests/test_opportunity_detector.py`

**Tests:** `backend/intelligence/opportunity_detector.py`

```
Checks:
1. Narrative with relevance_to_persona > 0.6 AND DNA element → returns ApprovedTopicBrief
2. Narrative with relevance_to_persona < 0.6 → discarded (not in output)
3. Narrative with high relevance but no DNA element → discarded
4. Generic trend topic ("Top 10 productivity tips") → discarded by DNA check
5. Technical narrative with consequence ("AI tools leaking credentials in generated code") → approved
6. ApprovedTopicBrief has all required fields: topic, angle, dna_element, target_accounts, timing, platform_notes
7. target_accounts is a list (can be multiple accounts)
8. Multiple narratives input → only qualifying ones returned
9. Empty narrative list input → returns empty list, no crash
10. Hard stop topic from persona.md → discarded even if DNA passes
```

---

## `scripts/tests/test_scorer.py`

**Tests:** `backend/intelligence/scorer.py`

```
Checks:
1. score_post(T=1.0, H=1.0, P=1.0) → score close to 1.0 (high inputs = high score)
2. score_post(T=0.0, H=0.0, P=0.0) → score close to 0.0 (low inputs = low score)
3. score_post(T=0.5, H=0.5, P=0.5) → score around 0.5 (midpoint)
4. Output is always between 0.0 and 1.0 (sigmoid constraint)
5. Higher hook_strength always produces higher score than lower (all else equal)
6. Higher topicality always produces higher score (all else equal)
7. Higher persona_alignment always produces higher score (all else equal)
8. Top 1-2 selection from a list of 10 candidates → returns exactly 1-2 highest scored
9. Rejected candidates are logged with rejection reason (check return structure)
10. Score values are stored correctly in Post record fields (score_topicality, score_hook, score_persona, score_total)
```

---

## `scripts/tests/test_brand_voice_guardian.py`

**Tests:** `backend/brand_voice_guardian/checker.py`

```
Checks:
1. Post with no DNA element → CheckResult.rejected=True, rejection_reason mentions DNA
2. Post with hard stop topic (e.g. "politics", "religion") → rejected immediately
3. Post that sounds nothing like Ahmad (generic corporate text) → rejected (tone_similarity < 0.55)
4. Post that's too long for LinkedIn (>1300 chars) → near_pass with edit suggestion about length
5. Well-written technical post in Ahmad's voice with consequence → passed=True
6. Near-pass posts have edit_suggestion populated (not empty)
7. Rejected posts have rejection_reason populated (not empty)
8. CheckResult has all required fields: passed, near_pass, rejected, edit_suggestion, rejection_reason
9. Checks run IN ORDER (DNA first — verify by checking which rejection_reason appears for DNA-failing post)
10. Function handles empty string input without crashing → rejected with appropriate reason
```

---

## `scripts/tests/test_persona_builder.py`

**Tests:** `backend/persona_engine/builder.py`

```
Checks:
1. Given a complete set of Stage 1 answers → persona.md file is created at correct path
2. persona.md contains all required sections (Identity, Voice & Tone, Audience, Content Pillars, Platform Behaviour, Engagement Style, Performance Memory)
3. Values from answers are correctly embedded in the file (spot-check 3 specific values)
4. Hard stops from answers appear in the Hard stops section
5. Vocabulary always/never used lists are populated from answers
6. Per-account tone modifiers section exists for all 4 accounts
7. Strategy History section exists with Version 1 entry
8. simulation_log.md is created at correct path with correct header
9. simulation_log.md is empty (no entries yet) after builder runs
10. If persona.md already exists, builder does NOT overwrite — it returns an error or warning
```

---

## `scripts/tests/test_prompt_builder.py`

**Tests:** `backend/persona_engine/prompt_builder.py`

```
Checks:
1. Returns both system_prompt and user_prompt (not just one string)
2. System prompt contains brand voice section from persona.md
3. System prompt contains hard stops (verify one hard stop appears)
4. System prompt contains the winning post structure (real situation → system insight → constraint → relatable framing → CTA)
5. System prompt contains Content DNA requirement instruction
6. Platform tone modifier for LinkedIn is different from Instagram personal tone modifier
7. Last 10 simulation_log entries are included in the prompt
8. user_prompt contains the topic brief content
9. Prompt requests 5–20 variants explicitly
10. Total prompt length is under 8000 tokens (don't exceed context limits)
```

---

## `scripts/tests/test_sim_engine.py`

**Tests:** `backend/onboarding/sim_engine.py`

```
Checks (use mock platform data — don't make real API calls):
1. Given declared interests → returns a scenario with correct structure (platform, scenario_type, shown_content)
2. scenario_type is one of the 5 valid types: trending_post_reaction, comment_reply_test, trend_format_test, controversy_response_test, meme_adaptation_test
3. Given user reaction + decision → generates "what AI learned" inference (not empty)
4. Appends to simulation_log.md correctly (new entry added, existing entries not touched)
5. simulation_log.md entry has all required fields (Platform, Scenario type, Shown, Reaction, Decision, What AI learned)
6. Running sim_engine 3 times → 3 entries in simulation_log.md (not 1 or 30)
7. simulation_log.md is NEVER truncated — existing content preserved after each append
8. What AI learned inference is specific to the input (not generic boilerplate)
9. Entry format matches the exact markdown structure defined in AGENTS.md
10. sim_engine handles missing/empty user response without crashing
```

---

## `scripts/tests/test_learning_engine.py`

**Tests:** `backend/feedback_loop/learning_engine.py`

```
Checks (use test DB records — clean up after):
1. compute_engagement_score(saves=10, shares=5, comments=8, follows=3) → exactly 10*5 + 5*3 + 8*2 + 3*5 = 96
2. compute_engagement_score(saves=0, shares=0, comments=0, follows=0) → 0
3. Post tagged correctly after scoring: hook_type, topic_pillar, format, account all populated
4. PatternDB record created/updated after enough posts for a combination (minimum 10)
5. Pattern detection: given 15 posts all with high scores for "consequence" hook → consequence identified as winning pattern
6. Pattern detection: given 15 posts all with low scores for "generic_tips" topic → flagged as underperforming
7. persona.md NOT updated when triggers are not met (< 14 days, < 30 posts, no engagement drop)
8. persona.md IS updated when time trigger fires (mock 14-day elapsed)
9. Strategy History in persona.md gets new version entry after update
10. mirofish_refiner called with refinement signal after learning cycle (verify signal is not empty)
```

---

## `scripts/tests/test_mirofish_seed_builder.py`

**Tests:** `backend/intelligence/mirofish/seed_builder.py`

```
Checks:
1. Returns a list of seed documents (not empty)
2. Each seed document has: title, content, source, timestamp
3. Minimum 10 documents returned (not just 1-2)
4. Documents from at least 2 different sources (RSS + Reddit or RSS + Trends)
5. No document has empty content field
6. Timestamps are valid ISO format
7. Content is reasonably relevant to niche keywords passed in (spot check)
8. Function handles RSS feed timeout gracefully (mock a timeout) → skips that feed, continues
9. Function handles PRAW rate limit gracefully → skips Reddit, continues with other sources
10. Total execution time under 60 seconds (don't hang forever on slow feeds)
```

---

## `scripts/tests/test_mirofish_graph_builder.py`

**Tests:** `backend/intelligence/mirofish/graph_builder.py`

```
Checks (use 5 mock seed documents):
1. Returns a knowledge graph object (not None, not empty dict)
2. Graph contains entities (at least 3 entities from 5 seed docs)
3. Graph contains relationships between entities (at least 1 relationship)
4. Community clusters detected (at least 1 cluster)
5. Entity types are classified (company, person, event, concept, trend)
6. Each entity has: name, type, relevance_score
7. Each relationship has: source_entity, target_entity, relationship_type
8. Graph output is serializable to JSON (for storage)
9. Function handles seed docs with no extractable entities gracefully (returns minimal graph, no crash)
10. Execution time under 120 seconds for 5 seed docs
```

---

## `scripts/tests/test_mirofish_pre_publish_gate.py`

**Tests:** `backend/intelligence/mirofish/pre_publish_gate.py`

```
Checks (use mock post text — no full simulation needed, mock simulation_runner):
1. Returns GateResult object with all required fields: decision, confidence, predicted_saves, predicted_comments, failure_reason, recommended_delay, early_learning_signal
2. decision is one of: "pass", "fail", "delay"
3. confidence is between 0.0 and 1.0
4. early_learning_signal is not empty (has hook_effectiveness, topic_resonance, persona_alignment, predicted_engagement_score)
5. PASS result: failure_reason is None, recommended_delay is None
6. FAIL result: failure_reason is populated (not empty string)
7. DELAY result: recommended_delay is a valid future datetime
8. Early learning signal is sent to learning engine immediately (mock learning_engine.receive_pre_signal and verify it's called)
9. High-quality post (clear consequence, Ahmad's voice) → decision=pass
10. Vague post ("Working on something exciting") → decision=fail
```

---

## `scripts/tests/test_persona_updater.py`

**Tests:** `backend/persona_engine/updater.py`

```
Checks:
1. Performance memory table updated with new post data
2. Content pillar weights rebalanced when one pillar significantly outperforms (mock PatternDB data)
3. Strategy History gets new version entry after update
4. Current strategy focus updated in persona.md
5. Next rotation check date updated in persona.md
6. persona.md is valid markdown after update (not corrupted)
7. All original sections preserved — updater only patches, never deletes sections
8. Version number increments correctly (Version 2, 3, 4...)
9. Update with no changes needed → persona.md unchanged (no spurious version bump)
10. Rotation trigger fires correctly when engagement drops >20% over 5 consecutive posts (mock data)
```

---

---

# AGENT B — Test Scripts to Build

---

## `scripts/tests/test_token_store.py`

**Tests:** `backend/token_store/store.py`

```
Checks (use test_ prefixed keys, clean up after):
1. save_token stores encrypted value (raw value not visible in DB)
2. get_token returns decrypted value matching what was saved
3. Saving same account+type twice → updates (not duplicates)
4. delete_token removes the record
5. get_token on non-existent token → returns None (not crash)
6. Encryption uses SECRET_KEY from env (not hardcoded)
7. Token with expiry set → expiry field saved correctly
8. All 4 account names accepted: instagram_personal, instagram_brand, facebook, linkedin
9. Token type validation: access_token and refresh_token both accepted
10. Round trip test: save → get → compare → exact match
```

---

## `scripts/tests/test_publishers.py`

**Tests:** All 4 publisher modules

**⚠️ Use DRY RUN mode — do NOT actually post to platforms during tests.**
Each publisher must accept a `dry_run=True` parameter that builds and validates the API payload but does NOT make the actual API call.

```
Instagram Personal checks:
1. Single image payload correctly structured (image_url, caption, access_token present)
2. Carousel payload has correct multi-step structure (items array, carousel container, publish)
3. Reel payload has media_type=REELS
4. Story payload has media_type=STORIES
5. dry_run=True → no HTTP request made (mock requests and verify not called)
6. Missing access token → raises clear error (not silent failure)

Instagram Brand checks:
7. Uses INSTAGRAM_BRAND_ACCESS_TOKEN (not personal token)
8. Same format support as personal (dry_run)

Facebook checks:
9. Text post payload has correct structure (message, access_token, page_id)
10. Uses page access token (not user token)

LinkedIn checks:
11. ugcPosts payload has author=urn:li:person:{id}, lifecycleState=PUBLISHED
12. Image upload is a 3-step flow (register → upload → post)
13. Header X-Restli-Protocol-Version: 2.0.0 present

Dispatcher checks:
14. Routes to instagram_personal.py when account=instagram_personal
15. Routes to all correct publishers for each account value
16. Returns result dict with success/failure per account
```

---

## `scripts/tests/test_token_refresher.py`

**Tests:** `backend/token_store/refresher.py`

```
Checks (mock HTTP calls — don't hit real OAuth endpoints):
1. Token expiring in 6 days → refresh triggered (within 7-day window)
2. Token expiring in 8 days → refresh NOT triggered (outside window)
3. Token already expired → refresh triggered + warning logged
4. Successful refresh → new token saved to token_store
5. Failed refresh (mock HTTP 400) → error logged, Notification record created
6. TokenRefreshLog record created for every attempt (success and failure)
7. TokenRefreshLog has: account, token_type, success, error_message, refreshed_at
8. All 4 accounts checked in a single refresher run
9. Refresher handles missing token gracefully (no token saved yet) → skips, no crash
10. New token expiry date saved correctly after refresh
```

---

## `scripts/tests/test_carousel_renderer.py`

**Tests:** `backend/render_engine/carousel.py`

```
Checks:
1. Given valid context → produces JPEG files at correct output path
2. Output files exist on disk after render (not just a path string)
3. Output image dimensions are exactly 1080x1080 pixels
4. Each slide generates a separate JPEG file (5 slides → 5 files)
5. Files are valid JPEGs (can be opened as images, not corrupted)
6. File size is reasonable (> 10KB, < 5MB per slide)
7. Brand colors from context appear in rendered image (basic color detection)
8. Template loads correctly for each account type: personal_ig, brand_ig, linkedin
9. Temp files cleaned up after render (no leftover temp_*.html files)
10. Function handles missing template gracefully → raises FileNotFoundError with clear message
```

---

## `scripts/tests/test_video_renderer.py`

**Tests:** `backend/render_engine/video.py`

```
Checks:
1. Remotion CLI is installed and accessible (npx remotion --version exits 0)
2. Given valid props → .mp4 file produced at output_path
3. Output file exists on disk
4. Output file is a valid .mp4 (ffprobe can read it without errors)
5. Instagram Reel output → aspect ratio is 9:16 (1080x1920)
6. Facebook video output → aspect ratio is 16:9 (1280x720)
7. Output file has video stream (not audio-only)
8. Duration matches expected (script timing)
9. ffmpeg post-processing runs without errors (check returncode=0)
10. Cleanup: temp Remotion frames deleted after render
```

---

## `scripts/tests/test_image_generator.py`

**Tests:** `backend/render_engine/image.py`

```
Checks (makes real Pollinations.ai call — free, no cost):
1. Returns a local file path (not a URL)
2. File exists on disk at returned path
3. File is a valid image (can be opened)
4. File dimensions match requested width/height (within 5% tolerance)
5. File size > 50KB (not a placeholder or empty)
6. Different prompts produce different images (hash comparison)
7. Request with width=1080, height=1080 → square image
8. Request with width=1080, height=1920 → portrait image
9. Function handles Pollinations timeout gracefully → retries once, then raises
10. enhance=true parameter included in request URL
```

---

## `scripts/tests/test_image_prompt_builder.py`

**Tests:** `backend/render_engine/prompt_builder.py`

```
Checks:
1. Returns a string (the prompt)
2. Prompt length is between 100 and 300 words (detailed but not excessive)
3. Prompt includes style/mood language (not just subject description)
4. Prompt includes color information from persona.md visual identity
5. Prompt includes platform-appropriate aspect ratio guidance
6. Different account_types produce different prompts (personal_ig vs brand_ig)
7. Different post briefs produce different prompts
8. Prompt does not contain markdown formatting (no ** or # — just plain text)
9. Quality markers included (e.g. "high resolution", "sharp", "professional")
10. Hard stops from persona.md don't appear as visual subjects in prompt
```

---

## `scripts/tests/test_content_generator.py`

**Tests:** `backend/content/generator.py`

```
Checks (makes real OpenRouter call — uses OPENROUTER_API_KEY):
1. Returns a list of strings (post variants)
2. Minimum 5 variants returned
3. Maximum 20 variants returned
4. Each variant is a non-empty string
5. Variants are meaningfully different from each other (not identical with minor word changes)
6. Generated content does not contain markdown code blocks or HTML tags
7. LinkedIn variants respect ~1300 char limit
8. Instagram variants have a strong first line (hook)
9. Model used is OPENROUTER_DEFAULT_MODEL from env (check response headers or log)
10. Retry logic works: mock a 429 response on first call → second call succeeds
```

---

## `scripts/tests/test_repurposer.py`

**Tests:** `backend/content/repurposer.py`

```
Checks (uses real OpenRouter call — one call):
1. Given a blog post text → returns dict with 4 keys: linkedin, instagram_personal, instagram_brand, facebook
2. All 4 keys present in output dict
3. All 4 values are non-empty strings
4. LinkedIn version is under 1300 chars
5. LinkedIn version reads like a LinkedIn post (professional register, lessons/insights angle)
6. Instagram personal version is noticeably more casual than LinkedIn version
7. Instagram brand version mentions Nyvora or brand context (not purely personal)
8. Facebook version ends with a discussion question
9. All 4 versions are thematically related to the input blog post
10. Function handles very short input (<100 words) without crashing
```

---

## `scripts/tests/test_scheduler_queue.py`

**Tests:** `backend/scheduler_worker/queue.py`

```
Checks (uses test queue.db in /tmp — clean up after):
1. add_job creates a record with status=pending
2. get_due_jobs returns jobs where scheduled_at <= now and status=pending
3. get_due_jobs does NOT return future-scheduled jobs
4. get_due_jobs does NOT return jobs with status=done or failed
5. mark_running updates status to running
6. mark_done updates status to done
7. mark_failed updates status to failed and saves error message
8. increment_attempts increments the attempts counter
9. Jobs with attempts >= 3 NOT returned by get_due_jobs
10. Concurrent safety: two processes calling get_due_jobs simultaneously don't return the same job (basic row locking)
```

---

## `scripts/tests/test_scheduler_dispatcher.py`

**Tests:** `backend/scheduler_worker/dispatcher.py`

```
Checks (mock publishers — don't actually post):
1. Due job found → publisher.dispatcher called with correct post_id and account
2. Successful publish → job marked done
3. Publisher raises exception → job marked failed, error saved
4. Job with attempts=2 and failed → retried (rescheduled with backoff)
5. Job with attempts=3 and failed → marked failed_final, Notification created
6. Backoff timing: attempt 1 fail → reschedule +5min, attempt 2 → +15min, attempt 3 → +45min
7. No due jobs → dispatcher runs cleanly without error
8. Multiple due jobs → all processed in single run
9. dispatcher respects per-account automation level (full_auto: dispatches immediately, manual: skips)
10. Dispatch result logged correctly for each job
```

---

## `scripts/tests/test_analytics_aggregator.py`

**Tests:** `backend/analytics/aggregator.py`

```
Checks (mock platform API calls — don't hit real APIs):
1. Given a published post_id → PostAnalytics record created
2. reach field populated (not 0 or None)
3. impressions field populated
4. likes, comments, shares, saves fields populated
5. PostAnalytics.engagement_score = saves*5 + shares*3 + comments*2 + follows*5 (verify formula)
6. Post record updated with analytics_collected=True after aggregation
7. Posts with published_at < 48h ago → skipped (too early for stable metrics)
8. Posts already marked analytics_collected=True → skipped (not double-collected)
9. Platform API error (mock 500) → error logged, post marked for retry, other posts continue
10. All 4 accounts aggregated in a single run
```

---

## `scripts/tests/test_reply_manager.py`

**Tests:** `backend/reply_manager/monitor.py`, `drafter.py`, `sender.py`

```
Monitor checks (mock platform API):
1. New comments found → Reply records created with status=pending_approval
2. Already-seen comments (by platform_comment_id) → NOT duplicated
3. comment_type classification: "Amazing post!" → praise, "How did you do this?" → question, "This is wrong" → criticism
4. Spam detection: "Buy followers now" → classified as spam, skipped
5. Reply records have all fields: post_id, account, platform_comment_id, comment_text, comment_type

Drafter checks (uses real OpenRouter call):
6. Draft reply generated for a question comment
7. Draft reply is in Ahmad's voice (not generic corporate)
8. LinkedIn reply draft is more formal than Instagram reply draft
9. draft_reply field populated in Reply record
10. Reply status updated to draft_ready after drafting

Sender checks (mock platform API call):
11. Approved reply → correct platform API called
12. Instagram reply uses correct endpoint: POST /{comment-id}/replies
13. LinkedIn reply uses correct endpoint: POST /v2/socialActions/{post-urn}/comments
14. Reply status updated to sent after successful send
15. sent_at timestamp recorded
```

---

## `scripts/tests/test_api_endpoints.py`

**Tests:** All FastAPI endpoints (both agents' endpoints)

Uses `httpx` to hit the running API. Start the API before running this test.

```
Auth checks:
1. POST /api/auth/login with valid credentials → returns JWT token
2. POST /api/auth/login with wrong credentials → 401
3. GET /api/auth/me with valid token → returns user data
4. Request without token to protected endpoint → 401

Content checks:
5. POST /api/content/generate with topic brief → returns list of variants
6. GET /api/content/drafts → returns list (empty or posts)
7. POST /api/content/:id/approve → status changes to approved
8. DELETE /api/content/:id → post deleted

Intelligence checks:
9. GET /api/intelligence/feed → returns narrative forecast (even if empty)
10. GET /api/intelligence/trends → returns trend signals

Scheduler checks:
11. POST /api/scheduler/schedule with post_id and datetime → job created
12. GET /api/scheduler → returns calendar posts

Analytics checks:
13. GET /api/analytics/overview → returns cross-account summary structure
14. GET /api/analytics/top → returns list (empty or posts)

Settings checks:
15. GET /api/settings/accounts → returns 4 accounts with status fields
16. GET /api/settings/automation → returns automation level per account
17. PATCH /api/settings/automation → updates level correctly

Persona checks:
18. GET /api/persona → returns persona.md content
19. GET /api/persona/export → returns file download (Content-Disposition header present)

Error handling:
20. GET /api/content/99999999 (non-existent ID) → 404 not 500
```

---

## `scripts/tests/test_full_pipeline.py`

**Tests:** The complete end-to-end flow — both agents' modules working together.

This is the integration test. Run this LAST after all individual tests pass.

```
Full pipeline test (dry_run=True on all publishers):

Step 1 — Seed collection
  Check: seed_builder returns documents

Step 2 — Opportunity detection
  Check: at least 1 topic brief approved from mock MiroFish output

Step 3 — Content generation
  Check: variants generated for approved brief

Step 4 — Scoring
  Check: top 1-2 candidates selected, scores populated

Step 5 — Brand Voice Guardian
  Check: at least 1 candidate passes guardian

Step 6 — Carousel render
  Check: carousel JPEGs produced for Instagram brief

Step 7 — Pre-publish gate
  Check: gate runs, returns decision (pass/fail/delay)

Step 8 — Schedule
  Check: post added to scheduler queue with correct scheduled_at

Step 9 — Dispatch (dry_run)
  Check: publisher called with correct payload, no actual API call made

Step 10 — Analytics mock
  Check: PostAnalytics record created with correct engagement_score formula

Step 11 — Learning engine
  Check: pattern detection runs, PatternDB updated

Step 12 — Persona check
  Check: persona.md exists and is valid after full cycle

Full pipeline result: ALL 12 steps must pass for overall PASS
```

---

## Running All Tests

```bash
# Run individual module test
python scripts/tests/test_content_dna_checker.py

# Run all Agent A tests
python scripts/tests/test_content_dna_checker.py && \
python scripts/tests/test_opportunity_detector.py && \
python scripts/tests/test_scorer.py && \
python scripts/tests/test_brand_voice_guardian.py && \
python scripts/tests/test_persona_builder.py && \
python scripts/tests/test_prompt_builder.py && \
python scripts/tests/test_sim_engine.py && \
python scripts/tests/test_learning_engine.py && \
python scripts/tests/test_mirofish_seed_builder.py && \
python scripts/tests/test_mirofish_graph_builder.py && \
python scripts/tests/test_mirofish_pre_publish_gate.py && \
python scripts/tests/test_persona_updater.py
echo "Agent A tests complete"

# Run all Agent B tests
python scripts/tests/test_token_store.py && \
python scripts/tests/test_publishers.py && \
python scripts/tests/test_token_refresher.py && \
python scripts/tests/test_carousel_renderer.py && \
python scripts/tests/test_video_renderer.py && \
python scripts/tests/test_image_generator.py && \
python scripts/tests/test_image_prompt_builder.py && \
python scripts/tests/test_content_generator.py && \
python scripts/tests/test_repurposer.py && \
python scripts/tests/test_scheduler_queue.py && \
python scripts/tests/test_scheduler_dispatcher.py && \
python scripts/tests/test_analytics_aggregator.py && \
python scripts/tests/test_reply_manager.py
echo "Agent B tests complete"

# Run API tests (requires running API)
uvicorn backend.main:app &
sleep 3
python scripts/tests/test_api_endpoints.py
echo "API tests complete"

# Run full integration test (run this last)
python scripts/tests/test_full_pipeline.py
echo "Integration test complete"
```

---

## What Counts as Done

A module is DONE when:
- Its test script runs to completion without crashing
- All checks in its test script show ✅ PASS
- The test script exits with code 0

A phase is DONE when:
- All modules in that phase have passing test scripts
- The full_pipeline test passes end-to-end

**Do not move to the next phase until the current phase's tests all pass.**
