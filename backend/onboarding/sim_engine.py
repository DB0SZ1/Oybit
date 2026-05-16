"""
Onboarding Simulation Engine — Agent A Module

Pulls real posts (or mock data), presents scenarios, logs decisions.
Records every reaction + decision + typed response.
Generates AI inference: "What AI learned" from each response.
APPENDS to simulation_log.md (NEVER overwrites).
"""

import os
import re
import json
import random
import glob
from datetime import datetime
from dataclasses import dataclass, field

# Try httpx for OpenRouter calls
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


VALID_SCENARIO_TYPES = [
    "trending_post_reaction",
    "comment_reply_test",
    "trend_format_test",
    "controversy_response_test",
    "meme_adaptation_test",
]

from backend.db.session import SessionLocal
from backend.db.models import TrendSignal

@dataclass
class Scenario:
    """A simulation scenario presented to the user."""
    platform: str
    scenario_type: str
    shown_content: str
    context: str = ""


@dataclass
class SimResult:
    """Result of a simulation interaction."""
    scenario: Scenario
    user_reaction: str
    user_decision: str
    ai_learned: str
    sim_number: int = 0


def _generate_ai_inference(scenario: Scenario, reaction: str, decision: str) -> str:
    """Generate 'What AI learned' from the user's response."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    if api_key and HAS_HTTPX:
        try:
            prompt = f"""Based on this simulation scenario and the user's response, generate a brief insight about what this reveals about their content voice, preferences, and instincts.

Scenario type: {scenario.scenario_type}
Platform: {scenario.platform}
Content shown: {scenario.shown_content}
User's reaction: {reaction}
User's decision: {decision}

Write 2-3 sentences about what this reveals about the user's voice, content philosophy, and engagement instincts. Be specific to their actual response. Start directly with the insight, no preamble."""

            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://oybit.nyvora.com",
                    "X-Title": "Oybit",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout:free"),
                    "messages": [
                        {"role": "system", "content": "You are a persona analysis expert. Generate brief, specific insights."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
    
    # Fallback: generate inference based on scenario type and response keywords
    return _generate_local_inference(scenario, reaction, decision)


def _generate_local_inference(scenario: Scenario, reaction: str, decision: str) -> str:
    """Generate AI inference locally without API call."""
    reaction_lower = (reaction + " " + decision).lower()
    
    inferences = []
    
    # Detect engagement style
    if any(w in reaction_lower for w in ["ignore", "skip", "wouldn't", "no", "pass"]):
        inferences.append("Shows selectivity — doesn't engage with everything, only topics that align with their authentic voice.")
    elif any(w in reaction_lower for w in ["adapt", "similar", "create", "my angle", "my version"]):
        inferences.append("Adapts trending content by adding personal proof and unique perspective rather than copying directly.")
    elif any(w in reaction_lower for w in ["engage", "reply", "respond", "address"]):
        inferences.append("Engages directly when the topic is relevant, prefers substance over avoidance.")
    
    # Detect voice preferences
    if any(w in reaction_lower for w in ["proof", "evidence", "built", "shipped", "real"]):
        inferences.append("Uses personal proof and tangible evidence rather than theory or generic advice.")
    if any(w in reaction_lower for w in ["personal", "story", "experience", "my"]):
        inferences.append("Prefers first-person storytelling anchored in real experience.")
    if any(w in reaction_lower for w in ["direct", "honest", "blunt", "straight"]):
        inferences.append("Communication style is direct and non-defensive.")
    
    if not inferences:
        inferences.append(f"Responded to {scenario.scenario_type.replace('_', ' ')} on {scenario.platform} with a considered response.")
    
    return " ".join(inferences[:3])


def fetch_public_content_bank_scenarios(identity_answers: dict) -> list:
    """
    (GAPS_FINAL 5.3) Gets relevant scenarios based on user identity for public mode 
    when accounts aren't connected.
    """
    bank_dir = os.path.join(os.path.dirname(__file__), "scenario_bank")
    if not os.path.exists(bank_dir):
        return []
        
    all_files = glob.glob(os.path.join(bank_dir, "*.json"))
    scenarios = []
    for fpath in all_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    scenarios.extend(data)
        except Exception:
            pass
            
    return [
        Scenario(
            platform=s.get("platform", "Unknown"), 
            scenario_type=s.get("scenario_type", "trending_post_reaction"), 
            shown_content=s.get("shown_content", ""), 
            context=s.get("context", "")
        ) 
        for s in scenarios if "shown_content" in s
    ]

def get_next_scenario(
    interests: list = None,
    scenario_type: str = None,
    used_scenarios: list = None,
    identity_answers: dict = None,
) -> Scenario:
    """
    Get the next simulation scenario.
    
    Args:
        interests: user's declared interests/niche keywords
        scenario_type: specific type to get (random if None)
        used_scenarios: list of already-used scenario indices to avoid
        identity_answers: answers from stage 1 to fetch curated scenarios
        
    Returns:
        Scenario object
    """
    if used_scenarios is None:
        used_scenarios = []
    
    # Select scenario type
    if scenario_type and scenario_type in VALID_SCENARIO_TYPES:
        stype = scenario_type
    else:
        stype = random.choice(VALID_SCENARIO_TYPES)
        
    # Check if we should use public curated scenarios
    scenarios = []
    if identity_answers:
        public_scenarios = fetch_public_content_bank_scenarios(identity_answers)
        filtered = [s for s in public_scenarios if s.scenario_type == stype]
        if filtered:
            s_obj = random.choice(filtered)
            return s_obj # Just return directly for public mode
    
    # Fetch real signals from the database
    db = SessionLocal()
    try:
        signals = db.query(TrendSignal).order_by(TrendSignal.created_at.desc()).limit(20).all()
        if not signals:
            # If database is completely empty, provide a generic fallback scenario
            return Scenario(
                platform="LinkedIn",
                scenario_type="trending_post_reaction",
                shown_content="[Real trends will appear here once the Trend Worker collects them from RSS/Social APIs]",
                context="System is awaiting real-time data collection."
            )
            
        # Pick a random signal from the recent ones
        idx = random.choice([i for i in range(len(signals)) if i not in used_scenarios] or list(range(len(signals))))
        sig = signals[idx]
        
        return Scenario(
            platform=sig.source,
            scenario_type=stype,
            shown_content=sig.title + "\n\n" + (sig.description or ""),
            context=f"Trend score: {sig.score}. Keywords: {sig.keywords}"
        )
    finally:
        db.close()


def process_sim_response(
    scenario: Scenario,
    reaction: str,
    decision: str,
    simulation_log_path: str,
    sim_number: int = None,
) -> SimResult:
    """
    Process user's reaction to a simulation scenario.
    
    Args:
        scenario: the scenario that was presented
        reaction: user's reaction text
        decision: user's decision text
        simulation_log_path: path to simulation_log.md
        sim_number: sim entry number (auto-incremented if None)
        
    Returns:
        SimResult with AI inference
    """
    # Handle empty/missing responses
    if not reaction:
        reaction = "(no reaction provided)"
    if not decision:
        decision = "(no decision provided)"
    
    # Generate AI inference
    ai_learned = _generate_ai_inference(scenario, reaction, decision)
    
    # Determine sim number
    if sim_number is None:
        sim_number = _get_next_sim_number(simulation_log_path)
    
    result = SimResult(
        scenario=scenario,
        user_reaction=reaction,
        user_decision=decision,
        ai_learned=ai_learned,
        sim_number=sim_number,
    )
    
    # Append to simulation_log.md (NEVER overwrite)
    _append_to_simulation_log(result, simulation_log_path)
    
    return result


def _get_next_sim_number(log_path: str) -> int:
    """Get the next sim number from the simulation log."""
    if not os.path.exists(log_path):
        return 1
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        numbers = re.findall(r'### Sim\s+(\d+)', content)
        if numbers:
            return max(int(n) for n in numbers) + 1
        return 1
    except Exception:
        return 1


def _append_to_simulation_log(result: SimResult, log_path: str):
    """Append a sim entry to simulation_log.md. NEVER overwrites existing content."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Check if we need a session header
    needs_session_header = True
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        if f"## Session {today}" in content:
            needs_session_header = False
    
    entry = ""
    if needs_session_header:
        entry += f"\n## Session {today}\n"
    
    entry += f"""
### Sim {result.sim_number:03d}
Platform: {result.scenario.platform}
Scenario type: {result.scenario.scenario_type}
Shown: {result.scenario.shown_content}
Reaction: {result.user_reaction}
Decision: {result.user_decision}
What AI learned: {result.ai_learned}
"""
    
    # APPEND only — never truncate, with file locking (OYBIT_GAP_SOLUTIONS 5.5)
    with open(log_path, "a", encoding="utf-8") as f:
        locked = False
        try:
            if os.name == 'nt':
                import msvcrt
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                    locked = True
                except Exception:
                    pass
            else:
                import fcntl
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    locked = True
                except Exception:
                    pass
                    
            f.write(entry)
            
        finally:
            if locked:
                if os.name == 'nt':
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                else:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except Exception:
                        pass
