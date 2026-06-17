"""
MiroFish Simulation Runner — Agent A Module
Runs multi-agent simulation where each agent "reads" a narrative
and produces an AI-generated reaction (engage/share/ignore/critique).

Uses OpenRouter for high-fidelity reactions on first batch,
then extrapolates for remaining agents to save API costs.
"""

import json
import re
import random
from dataclasses import dataclass, field
from logger import get_logger

logger = get_logger("mirofish.simulation_runner")


@dataclass
class AgentReaction:
    agent_id: str
    agent_type: str
    engaged: bool = False
    reaction_type: str = "ignore"  # engage, share, save, comment, ignore, critique
    comment_text: str = ""
    engagement_depth: float = 0.0  # 0-1, how deeply they engaged
    would_follow: bool = False


@dataclass
class SimulationResult:
    round_results: list = field(default_factory=list)
    resonance_score: float = 0.0
    confidence: float = 0.0
    save_prediction: int = 0
    comment_prediction: int = 0
    share_prediction: int = 0
    hook_score: float = 0.0
    topic_score: float = 0.0
    persona_score: float = 0.0
    predicted_engagement: int = 0
    failure_analysis: str = ""
    optimal_timing: str = ""
    timing_mismatch: bool = False
    agent_feedback: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "resonance_score": self.resonance_score,
            "confidence": self.confidence,
            "save_prediction": self.save_prediction,
            "comment_prediction": self.comment_prediction,
            "share_prediction": self.share_prediction,
            "hook_score": self.hook_score,
            "topic_score": self.topic_score,
            "persona_score": self.persona_score,
            "predicted_engagement": self.predicted_engagement,
            "failure_analysis": self.failure_analysis,
            "optimal_timing": self.optimal_timing,
            "agent_feedback": self.agent_feedback[:5],
        }


def _get_ai_reactions(agents_batch: list, narrative_text: str, platform: str) -> list:
    """
    Use OpenRouter to simulate how a batch of agents would react to a narrative.
    One API call covers multiple agents to minimize cost.
    """
    try:
        from llm.generator import call_openrouter_raw

        agent_descriptions = []
        for a in agents_batch:
            opinions = ""
            if hasattr(a, 'initial_opinions') and a.initial_opinions:
                reactions = a.initial_opinions.get("trending_reactions", [])
                if reactions:
                    opinions = f" Current opinions: {'; '.join(reactions[:2])}"

            agent_descriptions.append(
                f"- {a.agent_id} ({a.agent_type}): {a.personality}{opinions}"
            )

        prompt = (
            f"You are simulating {len(agents_batch)} social media users reacting to this {platform} post:\n\n"
            f'"""\n{narrative_text[:500]}\n"""\n\n'
            f"Users:\n" + "\n".join(agent_descriptions) + "\n\n"
            f"For each user, predict their reaction. Return ONLY valid JSON:\n"
            f'{{"reactions": [\n'
            f'  {{"agent_id": "agent_000", "reaction": "engage|share|save|comment|ignore|critique", '
            f'"engaged": true, "depth": 0.8, "would_follow": false, '
            f'"comment": "optional short comment if they would comment"}}\n'
            f"]}}\n"
            f'Each object in the reactions array MUST start with "agent_id": "agent_XXX". '
            f'Never omit the key name. Example: {{"agent_id": "agent_001", "reaction": ...}}.'
        )

        result = call_openrouter_raw(prompt, max_tokens=400)

        # Parse JSON from response
        # Handle cases where AI wraps in markdown code blocks
        cleaned = result.strip()
        if cleaned.startswith("```"):
            # Remove opening ``` line (possibly ```json)
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
            # Remove closing ```
            cleaned = re.sub(r'\n?```\s*$', '', cleaned)
            cleaned = cleaned.strip()

        # Fix common AI malformation: {"agent_001", -> {"agent_id": "agent_001",
        cleaned = re.sub(
            r'\{"(agent_\d+)",',
            r'{"agent_id": "\1",',
            cleaned
        )

        data = json.loads(cleaned)
        reactions = []
        for r in data.get("reactions", []):
            reactions.append(AgentReaction(
                agent_id=r.get("agent_id", "unknown"),
                agent_type=next((a.agent_type for a in agents_batch if a.agent_id == r.get("agent_id")), "unknown"),
                engaged=r.get("engaged", False),
                reaction_type=r.get("reaction", "ignore"),
                comment_text=r.get("comment", ""),
                engagement_depth=float(r.get("depth", 0.0)),
                would_follow=r.get("would_follow", False),
            ))
        return reactions

    except Exception as e:
        raw_output = result if 'result' in locals() else "Unknown (failed before generation)"
        logger.error(
            f"AI reaction generation failed — falling back to heuristic.\nRaw AI Response:\n{raw_output}",
            exc_info=True, 
            extra={"error": str(e)}
        )
        return []


def _heuristic_reaction(agent, narrative_text: str = "") -> AgentReaction:
    """
    Fallback heuristic when AI is unavailable.
    Uses agent personality traits + keyword matching for smarter reactions.
    """
    openness = getattr(agent, 'openness', 0.5)
    enthusiasm = getattr(agent, 'enthusiasm', 0.5)
    skepticism = getattr(agent, 'skepticism', 0.5)

    # Base engagement probability from personality traits
    engagement_prob = (openness * 0.4 + enthusiasm * 0.4 - skepticism * 0.2)

    # Boost if narrative contains keywords matching this agent's preferences
    preferences = getattr(agent, 'content_preferences', [])
    text_lower = narrative_text.lower() if narrative_text else ""
    keyword_boost = sum(0.05 for pref in preferences if pref.lower() in text_lower)
    engagement_prob = min(0.95, engagement_prob + keyword_boost)

    engaged = random.random() < engagement_prob

    if engaged:
        depth = random.uniform(0.3, 0.9)
        if depth > 0.7:
            reaction_type = random.choice(["share", "save", "comment"])
        else:
            reaction_type = "engage"
    else:
        depth = random.uniform(0.0, 0.2)
        if skepticism > 0.7 and random.random() < 0.3:
            reaction_type = "critique"
        else:
            reaction_type = "ignore"

    return AgentReaction(
        agent_id=getattr(agent, 'agent_id', 'unknown'),
        agent_type=getattr(agent, 'agent_type', 'unknown'),
        engaged=engaged,
        reaction_type=reaction_type,
        engagement_depth=round(depth, 3),
        would_follow=engaged and depth > 0.8 and random.random() < 0.2,
    )


def run_simulation(
    agents: list,
    narrative_text: str = "",
    platform: str = "linkedin",
    rounds: int = 2,
    ai_batch_size: int = 8,
) -> SimulationResult:
    """
    Run multi-agent simulation for a narrative.

    Strategy:
    - Round 1: Use AI for first batch of agents, heuristic for rest
    - Round 2: Use adjusted heuristics informed by Round 1 AI results
    This gives realistic reactions while keeping API costs low (1-2 calls per narrative).

    Args:
        agents: list of AgentConfig from agent_spawner
        narrative_text: the content to simulate reactions for
        platform: target platform for context
        rounds: number of simulation rounds
        ai_batch_size: number of agents to simulate with AI (rest use heuristic)

    Returns:
        SimulationResult with predictions and confidence scores
    """
    all_reactions = []
    agent_feedback = []

    for round_num in range(1, rounds + 1):
        round_reactions = []

        if round_num == 1 and narrative_text:
            # First round: AI for first batch, heuristic for rest
            ai_batch = agents[:ai_batch_size]
            heuristic_batch = agents[ai_batch_size:]

            # Get AI reactions for the first batch
            ai_reactions = _get_ai_reactions(ai_batch, narrative_text, platform)

            if ai_reactions:
                round_reactions.extend(ai_reactions)
                # Collect notable AI feedback for reporting
                for r in ai_reactions:
                    if r.comment_text:
                        agent_feedback.append({
                            "agent_type": r.agent_type,
                            "reaction": r.reaction_type,
                            "comment": r.comment_text,
                        })
            else:
                # AI failed — fall back to heuristic for all
                for agent in ai_batch:
                    round_reactions.append(_heuristic_reaction(agent, narrative_text))

            # Heuristic for remaining agents
            for agent in heuristic_batch:
                round_reactions.append(_heuristic_reaction(agent, narrative_text))
        else:
            # Subsequent rounds: all heuristic (agents "re-evaluate")
            for agent in agents:
                round_reactions.append(_heuristic_reaction(agent, narrative_text))

        all_reactions.extend(round_reactions)

    # Calculate aggregate metrics
    total = len(all_reactions)
    engaged_count = sum(1 for r in all_reactions if r.engaged)
    shares = sum(1 for r in all_reactions if r.reaction_type == "share")
    saves = sum(1 for r in all_reactions if r.reaction_type == "save")
    comments = sum(1 for r in all_reactions if r.reaction_type == "comment")
    critiques = sum(1 for r in all_reactions if r.reaction_type == "critique")
    follows = sum(1 for r in all_reactions if r.would_follow)

    resonance = engaged_count / max(total, 1)
    avg_depth = sum(r.engagement_depth for r in all_reactions) / max(total, 1)

    # Confidence is based on engagement quality, not just quantity
    confidence = min(0.95, resonance * 0.5 + avg_depth * 0.3 + (1 - critiques / max(total, 1)) * 0.2)

    # Failure analysis if low confidence
    failure_analysis = ""
    if confidence < 0.4:
        if critiques > engaged_count:
            failure_analysis = "High critique rate — content may be perceived as generic or hype-driven"
        elif resonance < 0.3:
            failure_analysis = "Low resonance — topic may not match audience interests"
        else:
            failure_analysis = "Mixed signals — consider refining hook or angle"

    result = SimulationResult(
        round_results=[{"round": i + 1, "reaction_count": len(all_reactions) // rounds} for i in range(rounds)],
        resonance_score=round(resonance, 3),
        confidence=round(confidence, 3),
        save_prediction=max(1, int(saves * 2.5)),
        comment_prediction=max(0, int(comments * 2)),
        share_prediction=max(0, int(shares * 2)),
        hook_score=round(avg_depth, 3),
        topic_score=round(resonance, 3),
        persona_score=round(1 - (critiques / max(total, 1)), 3),
        predicted_engagement=max(1, int(resonance * 100)),
        failure_analysis=failure_analysis,
        optimal_timing="09:00 WAT" if platform == "linkedin" else "12:00 WAT",
        agent_feedback=agent_feedback[:5],
    )

    logger.info("Simulation complete", extra={
        "agents": total,
        "engaged": engaged_count,
        "resonance": result.resonance_score,
        "confidence": result.confidence,
        "shares": shares,
        "saves": saves,
        "comments": comments,
        "critiques": critiques,
        "ai_reactions_used": bool(agent_feedback),
    })

    return result
