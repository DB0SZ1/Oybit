"""
MiroFish Narrative Forecaster — Agent A Module
Orchestrates the full daily pipeline: seed → graph → agents → simulation → report.
Produces narrative briefs that feed into the content generation pipeline.
"""

from backend.intelligence.mirofish.seed_builder import collect_seeds
from backend.intelligence.mirofish.graph_builder import build_graph
from backend.intelligence.mirofish.agent_spawner import spawn_agents
from backend.intelligence.mirofish.simulation_runner import run_simulation
from backend.intelligence.mirofish.report_agent import synthesize_report
from backend.logger import get_logger

logger = get_logger("mirofish.forecaster")


def run_daily_forecast(
    keywords: list = None,
    agent_count: int = None,
    refinement_signal: dict = None,
    target_platforms: list = None,
) -> dict:
    """
    Run the full MiroFish daily forecasting pipeline.

    Args:
        keywords: niche keywords for seed collection
        agent_count: number of simulation agents (defaults to MIROFISH_AGENT_COUNT env)
        refinement_signal: learning engine feedback for agent weighting
        target_platforms: platforms to simulate for (default: all)

    Returns:
        dict with narratives, graph data, simulation results, and intelligence report
    """
    if agent_count is None:
        from backend.config import MIROFISH_AGENT_COUNT
        agent_count = MIROFISH_AGENT_COUNT

    if target_platforms is None:
        target_platforms = ["linkedin", "instagram_personal"]

    logger.info("Starting MiroFish daily forecast", extra={
        "keywords": keywords,
        "agent_count": agent_count,
        "platforms": target_platforms,
    })

    # Step 1: Collect seeds from RSS, Reddit, and keyword trends
    seeds = collect_seeds(keywords=keywords)
    logger.info("Seeds collected", extra={"count": len(seeds)})

    if not seeds:
        logger.warning("No seeds collected — MiroFish pipeline will produce empty results")
        return {"narratives": [], "graph": {}, "simulation": {}, "report": {}}

    # Step 2: Build knowledge graph from seeds
    graph = build_graph(seeds)
    logger.info("Knowledge graph built", extra={
        "entities": len(graph.entities),
        "relationships": len(graph.relationships),
        "communities": len(graph.communities),
    })

    # Step 3: Spawn agents with graph context and learning engine feedback
    agents = spawn_agents(
        graph=graph,
        count=agent_count,
        refinement_signal=refinement_signal,
        enrich_with_ai=True,
    )
    logger.info("Agents spawned", extra={"count": len(agents)})

    # Step 4: Extract top narrative themes from graph communities
    narratives = _extract_narratives_from_graph(graph, seeds)

    # Step 5: Simulate each narrative across target platforms
    simulation_results = {}
    for narrative in narratives[:5]:  # Limit to top 5 narratives
        for platform in target_platforms:
            sim_key = f"{narrative['theme']}_{platform}"
            sim_result = run_simulation(
                agents=agents,
                narrative_text=narrative["text"],
                platform=platform,
                rounds=2,
            )
            simulation_results[sim_key] = {
                "narrative": narrative,
                "platform": platform,
                "result": sim_result.to_dict(),
                "confidence": sim_result.confidence,
                "resonance": sim_result.resonance_score,
            }

    # Step 6: Generate intelligence report
    report = synthesize_report(
        simulation_results=simulation_results,
        graph_data=graph,
    )

    result = {
        "narratives": narratives,
        "graph": graph.to_dict(),
        "simulation": simulation_results,
        "report": report.to_dict() if hasattr(report, 'to_dict') else report,
        "seed_count": len(seeds),
        "entity_count": len(graph.entities),
        "agent_count": len(agents),
    }

    logger.info("MiroFish daily forecast complete", extra={
        "narrative_count": len(narratives),
        "simulated": len(simulation_results),
        "top_confidence": max((s["confidence"] for s in simulation_results.values()), default=0),
    })

    return result


def _extract_narratives_from_graph(graph, seeds) -> list:
    """
    Extract narrative themes from the knowledge graph communities.
    Each narrative is a content opportunity that can be turned into a post.
    """
    narratives = []

    for community in graph.communities:
        if not community.entities:
            continue

        # Find seeds that mention entities in this community
        related_seeds = []
        for seed in seeds:
            text = f"{seed.title} {seed.content}".lower()
            if any(entity.lower() in text for entity in community.entities[:5]):
                related_seeds.append(seed)

        if related_seeds:
            # Build narrative from the most relevant seed
            best_seed = related_seeds[0]
            narrative_text = (
                f"Topic: {community.theme}. "
                f"Key entities: {', '.join(community.entities[:5])}. "
                f"Context: {best_seed.title}. {best_seed.content[:300]}"
            )

            narratives.append({
                "theme": community.theme,
                "text": narrative_text,
                "entities": community.entities[:5],
                "seed_sources": [s.source for s in related_seeds[:3]],
                "seed_count": len(related_seeds),
            })

    # Sort by seed count (more seeds = more active topic)
    narratives.sort(key=lambda n: n["seed_count"], reverse=True)

    return narratives
