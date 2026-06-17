"""
MiroFish Agent Spawner — Agent A Module
Generates agent personas from knowledge graph for simulation.

Uses OpenRouter to generate realistic audience personas based on
the knowledge graph entities and Ahmad's target audience profile.
Falls back to archetype-based generation if AI is unavailable.
"""

import random
import json
from dataclasses import dataclass, field
from logger import get_logger

logger = get_logger("mirofish.agent_spawner")

# Archetype templates — used as basis for AI refinement or as direct fallback
AGENT_ARCHETYPES = [
    {
        "type": "nigerian_developer",
        "personality": "Follows African tech closely, pragmatic, values proof over hype",
        "openness": 0.7, "skepticism": 0.3, "enthusiasm": 0.7,
        "platforms": ["linkedin", "instagram_personal"],
        "content_preferences": ["tutorials", "real stories", "African tech news"],
    },
    {
        "type": "indie_hacker",
        "personality": "Build-in-public advocate, ships fast, values authenticity",
        "openness": 0.8, "skepticism": 0.2, "enthusiasm": 0.8,
        "platforms": ["linkedin", "instagram_personal"],
        "content_preferences": ["building in public", "revenue updates", "founder stories"],
    },
    {
        "type": "linkedin_professional",
        "personality": "Career-focused, shares thought leadership, formal",
        "openness": 0.5, "skepticism": 0.5, "enthusiasm": 0.5,
        "platforms": ["linkedin"],
        "content_preferences": ["career advice", "industry insights", "leadership"],
    },
    {
        "type": "startup_founder",
        "personality": "Follows product and funding news, execution-oriented",
        "openness": 0.7, "skepticism": 0.4, "enthusiasm": 0.6,
        "platforms": ["linkedin", "instagram_personal"],
        "content_preferences": ["fundraising", "product launches", "growth tactics"],
    },
    {
        "type": "tech_enthusiast",
        "personality": "General interest, shares interesting finds, low barrier to engagement",
        "openness": 0.8, "skepticism": 0.2, "enthusiasm": 0.7,
        "platforms": ["instagram_personal", "facebook"],
        "content_preferences": ["AI tools", "interesting projects", "tech news"],
    },
    {
        "type": "skeptic",
        "personality": "Challenges hype, demands proof, contrarian but thoughtful",
        "openness": 0.3, "skepticism": 0.9, "enthusiasm": 0.2,
        "platforms": ["linkedin"],
        "content_preferences": ["critical analysis", "debunking", "data-driven takes"],
    },
    {
        "type": "early_adopter",
        "personality": "Uses AI tools daily, opinionated, tech-forward trendspotter",
        "openness": 0.9, "skepticism": 0.3, "enthusiasm": 0.9,
        "platforms": ["instagram_personal", "linkedin"],
        "content_preferences": ["new tools", "AI updates", "futurism"],
    },
    {
        "type": "african_entrepreneur",
        "personality": "Building in Africa, resourceful, community-driven, values local context",
        "openness": 0.7, "skepticism": 0.3, "enthusiasm": 0.8,
        "platforms": ["linkedin", "facebook", "instagram_personal"],
        "content_preferences": ["African startup ecosystem", "infrastructure", "local solutions"],
    },
    {
        "type": "security_engineer",
        "personality": "Laser-focused on security, values depth over breadth, cautious about hype",
        "openness": 0.4, "skepticism": 0.7, "enthusiasm": 0.4,
        "platforms": ["linkedin"],
        "content_preferences": ["cybersecurity", "breaches", "secure coding", "API security"],
    },
]


@dataclass
class AgentConfig:
    agent_id: str
    agent_type: str
    personality: str
    openness: float
    skepticism: float
    enthusiasm: float
    platforms: list = field(default_factory=list)
    content_preferences: list = field(default_factory=list)
    initial_opinions: dict = field(default_factory=dict)
    social_connections: list = field(default_factory=list)


def _enrich_agents_with_ai(agents: list, graph=None) -> list:
    """
    Use OpenRouter to enrich agent personas with context from the knowledge graph.
    This makes agents react more realistically to specific topics found in today's seeds.
    """
    if graph is None or not hasattr(graph, 'entities') or not graph.entities:
        return agents

    try:
        from llm.generator import call_openrouter_raw

        # Build context from graph entities
        trending_topics = [e.name for e in graph.entities if e.type == "trend"][:5]
        hot_companies = [e.name for e in graph.entities if e.type == "company"][:5]
        key_concepts = [e.name for e in graph.entities if e.type == "concept"][:5]

        if not (trending_topics or hot_companies or key_concepts):
            return agents

        context_summary = (
            f"Today's trending topics: {', '.join(trending_topics)}. "
            f"Companies in the news: {', '.join(hot_companies)}. "
            f"Key concepts: {', '.join(key_concepts)}."
        )

        # Enrich a subset of agents with topic-specific opinions
        for agent in agents[:10]:  # Only enrich first 10 to save API calls
            prompt = (
                f"You are simulating a social media user with this profile:\n"
                f"Type: {agent.agent_type}\n"
                f"Personality: {agent.personality}\n\n"
                f"Given these trending topics today: {context_summary}\n\n"
                f"Generate 2-3 short opinion statements this persona would have "
                f"about the trending topics. Return JSON only:\n"
                f'{{"opinions": ["opinion1", "opinion2"]}}'
            )

            try:
                result = call_openrouter_raw(prompt, max_tokens=150)
                data = json.loads(result)
                agent.initial_opinions = {
                    "trending_reactions": data.get("opinions", []),
                    "context": context_summary[:200],
                }
            except Exception:
                # AI enrichment is optional — continue without it
                pass

    except ImportError:
        logger.info("OpenRouter not available for agent enrichment — using base archetypes")

    return agents


def spawn_agents(
    graph=None,
    count: int = 20,
    refinement_signal: dict = None,
    enrich_with_ai: bool = True,
) -> list:
    """
    Generate agent personas from knowledge graph.

    Args:
        graph: KnowledgeGraph from graph_builder
        count: number of agents to spawn
        refinement_signal: feedback from learning engine to weight archetypes
        enrich_with_ai: whether to use OpenRouter for persona enrichment

    Returns:
        list of AgentConfig objects
    """
    agents = []

    # Weight archetypes based on refinement signal from learning engine
    weights = [1.0] * len(AGENT_ARCHETYPES)
    if refinement_signal:
        performing = refinement_signal.get("audience_response_patterns", {})
        underperforming = refinement_signal.get("underperforming_segments", {})

        for i, arch in enumerate(AGENT_ARCHETYPES):
            # Boost weights for audience segments that engage well with Ahmad's content
            for audience_key in performing:
                if arch["type"].replace("_", " ") in audience_key.lower():
                    weights[i] *= 1.5

            # Slightly reduce but don't eliminate underperforming segments
            for audience_key in underperforming:
                if arch["type"].replace("_", " ") in audience_key.lower():
                    weights[i] *= 0.7

    for i in range(count):
        arch = random.choices(AGENT_ARCHETYPES, weights=weights, k=1)[0]

        # Add controlled variation to personality traits
        jitter = lambda base: round(max(0.05, min(0.95, base + random.uniform(-0.1, 0.1))), 3)

        agent = AgentConfig(
            agent_id=f"agent_{i:03d}",
            agent_type=arch["type"],
            personality=arch["personality"],
            openness=jitter(arch["openness"]),
            skepticism=jitter(arch["skepticism"]),
            enthusiasm=jitter(arch["enthusiasm"]),
            platforms=arch.get("platforms", []),
            content_preferences=arch.get("content_preferences", []),
        )
        agents.append(agent)

    # Optionally enrich agents with AI-generated opinions about today's topics
    if enrich_with_ai and graph:
        agents = _enrich_agents_with_ai(agents, graph)

    logger.info("Agents spawned", extra={
        "count": len(agents),
        "types": {a.agent_type: sum(1 for x in agents if x.agent_type == a.agent_type) for a in agents},
        "ai_enriched": enrich_with_ai and graph is not None,
    })

    return agents
