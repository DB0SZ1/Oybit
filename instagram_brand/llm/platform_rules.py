"""
Oybit — Platform Rules Validator
Encapsulates strict formatting rules for LinkedIn and Instagram Reels.
(GAPS_FINAL 6.2 / 6.3)
"""
import re

def validate_reel_caption_hook(caption: str) -> dict:
    """
    Instagram Reel captions must have a strong hook in the first 125 chars 
    before the "See more" truncation.
    """
    if not caption:
        return {"passed": False, "suggestion": "Caption is empty."}
        
    # Get first line or first 125 chars
    first_line = caption.split('\n')[0][:125].strip()
    
    if len(first_line) < 15:
        return {
            "passed": False, 
            "suggestion": "The first line of the Reel caption is too short. It must act as a strong hook before truncation."
        }
        
    return {"passed": True, "suggestion": ""}

def check_linkedin_specific_rules(text: str) -> list:
    """
    LinkedIn specific hard rules:
    - Min 600 chars (for dwell time metric)
    - Max 1300 chars (readability)
    - Never start with "I" (too generic/egocentric)
    - Max 5 hashtags
    - Max 3 emojis
    """
    issues = []
    
    if not text:
        return ["Text is empty."]
        
    if len(text) < 600:
        issues.append("LinkedIn posts must be at least 600 characters to optimize for Dwell Time.")
        
    if len(text) > 1300:
        issues.append("LinkedIn posts should not exceed 1300 characters to maintain readability.")
        
    if text.lstrip().startswith("I "):
        issues.append("LinkedIn posts must not start with 'I '. Use a system insight or consequence hook instead.")
        
    hashtag_count = len(re.findall(r'#\w+', text))
    if hashtag_count > 5:
        issues.append(f"Too many hashtags ({hashtag_count}). Maximum allowed for LinkedIn is 5.")
        
    # Very basic emoji count heuristic (looking for non-ASCII, though not all non-ASCII are emojis)
    # A robust emoji counter would use the `emoji` library, but for MVP this is acceptable.
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
    emoji_count = len(emoji_pattern.findall(text))
    if emoji_count > 3:
        issues.append(f"Too many emojis ({emoji_count}). Maximum allowed for LinkedIn is 3.")
        
    return issues
