"""
Persona Updater — Agent A Module

Takes PatternDB data + feedback signal.
Implements 4 update triggers:
  1. Time-based: 14 days since last update → patch performance memory
  2. Engagement drop: avg score drops >20% over 5 consecutive posts → rotate strategy
  3. Post volume: every 30 posts → refresh performance memory
  4. Pattern shift: winning combo changes significantly → update pillar weights
"""

import os
import re
import tempfile
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class UpdateResult:
    """Result of a persona update attempt."""
    updated: bool
    version: int
    trigger: str
    changes: list
    error: str = None


def _read_persona(persona_path: str) -> str:
    """Read persona.md content."""
    with open(persona_path, "r", encoding="utf-8") as f:
        return f.read()


def _write_persona(persona_path: str, content: str):
    """Write persona.md content atomically to prevent corruption."""
    dir_name = os.path.dirname(persona_path)
    os.makedirs(dir_name, exist_ok=True)
    
    # Write to a temporary file in the same directory, then replace atomically
    fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=".persona_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        # Windows replace requires destination to not be in use, but is atomic on POSIX
        os.replace(temp_path, persona_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e


def _get_current_version(content: str) -> int:
    """Extract current version number from persona.md."""
    match = re.search(r'Version:\s*(\d+)', content)
    return int(match.group(1)) if match else 0


def _get_last_updated(content: str) -> datetime:
    """Extract last updated timestamp from persona.md."""
    match = re.search(r'Last updated:\s*(\S+)', content)
    if match:
        try:
            return datetime.fromisoformat(match.group(1))
        except ValueError:
            pass
    return datetime.min


def _update_version_header(content: str, new_version: int, strategy_focus: str = None) -> str:
    """Update the version header in persona.md."""
    now = datetime.utcnow().isoformat()
    replacement = f"Version: {new_version} | Last updated: {now}"
    if strategy_focus:
        replacement += f" | Strategy: {strategy_focus}"
    content = re.sub(
        r'Version:\s*\d+\s*\|\s*Last updated:\s*\S+(\s*\|\s*Strategy:\s*[^_]*)?',
        replacement,
        content,
    )
    return content


def _update_performance_memory(content: str, pattern_data: dict) -> str:
    """Update the performance memory table with new data."""
    for account, data in pattern_data.items():
        if not data:
            continue
        # Find and replace the row for this account
        account_label_map = {
            "instagram_personal": "Personal IG",
            "instagram_brand": "Brand IG",
            "linkedin": "LinkedIn",
            "facebook": "Facebook",
        }
        label = account_label_map.get(account, account)
        best_format = data.get("best_format", "—")
        best_pillar = data.get("best_pillar", "—")
        best_hook = data.get("best_hook_type", "—")
        avg_score = data.get("avg_engagement_score", "—")
        
        # Update top performing row
        pattern = rf'\|\s*{re.escape(label)}\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|'
        replacement = f"| {label} | {best_format} | {best_pillar} | {best_hook} | {avg_score} |"
        content = re.sub(pattern, replacement, content, count=1)
    
    return content


def _update_strategy_history(content: str, version: int, trigger: str, change: str) -> str:
    """Append a new entry to the Strategy History table."""
    date = datetime.utcnow().strftime("%Y-%m-%d")
    new_row = f"| {version} | {date} | {trigger} | {change} |"
    
    # Find the last row of the strategy history table and append after it
    # Match the pattern of table rows
    history_pattern = r'(\| \d+ \| [^|]+ \| [^|]+ \| [^|]+ \|)(?!\s*\n\s*\|)'
    matches = list(re.finditer(history_pattern, content))
    if matches:
        last_match = matches[-1]
        insert_pos = last_match.end()
        content = content[:insert_pos] + "\n" + new_row + content[insert_pos:]
    
    return content


def _update_next_rotation(content: str, days: int = 14) -> str:
    """Update the next rotation check date."""
    next_date = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
    content = re.sub(
        r'\*\*Next rotation check:\*\*\s*\S*',
        f"**Next rotation check:** {next_date}",
        content,
    )
    return content


def _update_strategy_focus(content: str, new_focus: str) -> str:
    """Update the current strategy focus."""
    content = re.sub(
        r'\*\*Current strategy focus:\*\*\s*.*',
        f"**Current strategy focus:** {new_focus}",
        content,
    )
    return content


def _update_pillar_weights(content: str, new_weights: dict) -> str:
    """Update content pillar posting weights based on performance data."""
    for pillar_name, weights in new_weights.items():
        # Find the pillar row and update percentages
        pattern = rf'(\|\s*{re.escape(pillar_name)}\s*\|[^|]*\|)\s*(\d+)%\s*\|\s*(\d+)%\s*\|\s*(\d+)%\s*\|\s*(\d+)%\s*\|'
        if weights:
            pig = weights.get("personal_ig", "25")
            big = weights.get("brand_ig", "25")
            li = weights.get("linkedin", "25")
            fb = weights.get("facebook", "25")
            replacement = rf'\g<1> {pig}% | {big}% | {li}% | {fb}% |'
            content = re.sub(pattern, replacement, content, count=1)
    
    return content


def check_triggers(
    persona_path: str,
    pattern_db_data: dict = None,
    recent_posts: list = None,
    total_posts_since_last: int = 0,
) -> dict:
    """
    Check which update triggers are active.
    
    Args:
        persona_path: path to persona.md
        pattern_db_data: aggregated PatternDB performance data
        recent_posts: list of recent post engagement scores
        total_posts_since_last: posts published since last update
        
    Returns:
        dict with trigger names and whether they fire
    """
    content = _read_persona(persona_path)
    last_updated = _get_last_updated(content)
    now = datetime.utcnow()
    
    triggers = {
        "time_based": False,
        "engagement_drop": False,
        "post_volume": False,
        "pattern_shift": False,
    }
    
    # 1. Time-based: 14 days since last update
    if (now - last_updated).days >= 14:
        triggers["time_based"] = True
    
    # 2. Engagement drop: avg score drops >20% over 5 consecutive posts
    if recent_posts and len(recent_posts) >= 5:
        last_5 = recent_posts[-5:]
        if len(recent_posts) > 5:
            previous = recent_posts[:-5]
            if previous:
                prev_avg = sum(previous) / len(previous)
                last_5_avg = sum(last_5) / len(last_5)
                if prev_avg > 0 and (prev_avg - last_5_avg) / prev_avg > 0.20:
                    triggers["engagement_drop"] = True
    
    # 3. Post volume: every 30 posts
    if total_posts_since_last >= 30:
        triggers["post_volume"] = True
    
    # 4. Pattern shift: winning combo changes (detected from pattern_db_data)
    if pattern_db_data and pattern_db_data.get("pattern_shift_detected", False):
        triggers["pattern_shift"] = True
    
    return triggers


def update_persona(
    persona_path: str,
    trigger: str,
    pattern_db_data: dict = None,
    new_strategy_focus: str = None,
    pillar_weights: dict = None,
    force: bool = False,
) -> UpdateResult:
    """
    Apply targeted patches to persona.md.
    
    Args:
        persona_path: path to persona.md
        trigger: which trigger caused this update (time_based, engagement_drop, post_volume, pattern_shift)
        pattern_db_data: performance data per account from PatternDB
        new_strategy_focus: if set, updates strategy focus
        pillar_weights: if set, updates content pillar weights
        force: if True, skip trigger validation
        
    Returns:
        UpdateResult with details of changes made
    """
    if not os.path.exists(persona_path):
        return UpdateResult(
            updated=False,
            version=0,
            trigger=trigger,
            changes=[],
            error="persona.md not found",
        )

    content = _read_persona(persona_path)
    original_content = content
    current_version = _get_current_version(content)
    new_version = current_version + 1
    changes = []

    # Apply updates based on trigger type
    if trigger == "time_based" or trigger == "post_volume":
        if pattern_db_data:
            content = _update_performance_memory(content, pattern_db_data)
            changes.append("Updated performance memory table")
        
    if trigger == "engagement_drop":
        if new_strategy_focus:
            content = _update_strategy_focus(content, new_strategy_focus)
            changes.append(f"Rotated strategy focus to: {new_strategy_focus}")
        else:
            content = _update_strategy_focus(content, "Engagement recovery — diversify hook styles and increase personal storytelling")
            changes.append("Auto-rotated strategy due to engagement drop")
        
    if trigger == "pattern_shift":
        if pillar_weights:
            content = _update_pillar_weights(content, pillar_weights)
            changes.append("Rebalanced content pillar weights")
        if pattern_db_data:
            content = _update_performance_memory(content, pattern_db_data)
            changes.append("Updated performance memory from new patterns")
    
    # If no changes were actually made to content, skip version bump
    if content == original_content and not force:
        return UpdateResult(
            updated=False,
            version=current_version,
            trigger=trigger,
            changes=[],
        )

    # Apply common updates
    change_desc = "; ".join(changes) if changes else "No specific changes"
    content = _update_strategy_history(content, new_version, trigger, change_desc)
    content = _update_next_rotation(content)
    content = _update_version_header(content, new_version, new_strategy_focus)

    # Write back
    _write_persona(persona_path, content)

    return UpdateResult(
        updated=True,
        version=new_version,
        trigger=trigger,
        changes=changes,
    )
