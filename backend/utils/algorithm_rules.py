"""
Oybit — Platform Algorithm Corrections (GAPs 8.1–8.3)
Encodes real platform algorithm behaviors that differ from common assumptions.
"""

# ── GAP 8.1: Instagram Algorithm Reality ───────────────────────
INSTAGRAM_RULES = {
    "reels_boost_window_hours": 48,       # Reels get boosted for 48h, not 24h
    "carousel_avg_engagement_multiplier": 1.4,  # Carousels outperform single images by ~40%
    "optimal_hashtag_count": (5, 15),     # 5-15 hashtags, not 30
    "story_frequency_cap_per_day": 5,     # More than 5 stories/day reduces reach
    "reel_optimal_length_seconds": (15, 30),   # 15-30s Reels perform best
    "caption_first_line_hook_chars": 125,  # First 125 chars shown before "more"
    "best_post_times_wat": ["07:00", "12:00", "18:00", "21:00"],
    "avoid_external_links": True,          # IG penalizes posts with external links
    "collab_posts_boost": True,            # Collab posts get 2x distribution
    "alt_text_seo_boost": True,            # Alt text improves discoverability
}

# ── GAP 8.2: LinkedIn Algorithm Reality ────────────────────────
LINKEDIN_RULES = {
    "first_hour_engagement_critical": True,  # First 60 min determines reach
    "dwell_time_weighted": True,           # Time spent reading > likes
    "optimal_post_length_chars": (1200, 3000),  # Long-form performs best
    "poll_engagement_multiplier": 2.5,     # Polls get 2.5x engagement
    "carousel_pdf_trick": True,            # PDF carousels get native treatment
    "newsletter_subscriber_boost": True,   # Newsletter editions boost profile
    "comment_within_first_hour": True,     # Creator should comment on own post
    "hashtag_count": (3, 5),               # 3-5 hashtags max
    "avoid_external_links_in_post": True,  # Put links in comments, not post body
    "best_post_times_wat": ["08:00", "10:00", "17:00"],
    "first_line_never_starts_with_i": True,  # Engagement drops when post starts with "I"
}

# ── GAP 8.3: Facebook Reality ──────────────────────────────────
FACEBOOK_RULES = {
    "organic_reach_percentage": 2.0,       # Only 2% of followers see organic posts
    "groups_reach_multiplier": 5.0,        # Group posts get 5x reach vs page posts
    "video_native_boost": True,            # Native video > YouTube links
    "reels_currently_boosted": True,       # Facebook is pushing Reels hard
    "link_posts_penalized": True,          # Links reduce distribution
    "optimal_post_frequency_per_day": 1,   # 1 post/day max for pages
    "best_post_times_wat": ["09:00", "13:00", "16:00"],
    "crosspost_from_ig_penalized": False,  # IG crossposts are fine on FB
}

def get_platform_rules(platform: str) -> dict:
    """Get algorithm rules for a platform."""
    rules_map = {
        "instagram_personal": INSTAGRAM_RULES,
        "instagram_brand": INSTAGRAM_RULES,
        "facebook": FACEBOOK_RULES,
        "linkedin": LINKEDIN_RULES,
    }
    return rules_map.get(platform, {})

def validate_against_rules(post_data: dict, platform: str) -> list[str]:
    """Validate a post against platform algorithm rules. Returns list of warnings."""
    rules = get_platform_rules(platform)
    warnings = []
    
    text = post_data.get("content_text", "")
    
    # LinkedIn first-line check
    if platform == "linkedin" and rules.get("first_line_never_starts_with_i"):
        first_line = text.split('\n')[0].strip() if text else ""
        if first_line.startswith("I ") or first_line.startswith("I'"):
            warnings.append("LinkedIn: First line starts with 'I' — engagement drops. Rewrite hook.")
    
    # External link check
    if rules.get("avoid_external_links") or rules.get("avoid_external_links_in_post"):
        import re
        if re.search(r'https?://', text):
            warnings.append(f"{platform}: External link detected in post body — move to comment.")
    
    # Instagram caption hook length
    if platform in ("instagram_personal", "instagram_brand"):
        hook_limit = rules.get("caption_first_line_hook_chars", 125)
        first_line = text.split('\n')[0] if text else ""
        if len(first_line) > hook_limit:
            warnings.append(f"Instagram: First line is {len(first_line)} chars, exceeds {hook_limit} char hook limit.")
    
    # Hashtag count
    if "hashtag_count" in rules:
        import re
        hashtags = re.findall(r'#\w+', text)
        min_h, max_h = rules["hashtag_count"]
        if len(hashtags) > max_h:
            warnings.append(f"{platform}: Too many hashtags ({len(hashtags)}). Optimal: {min_h}-{max_h}.")
    
    return warnings
