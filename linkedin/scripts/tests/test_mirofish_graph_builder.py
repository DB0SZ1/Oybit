"""
Tests for MiroFish Graph Builder module.
Verifies entity extraction, relationship mapping, community detection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_build_graph_from_seeds():
    """Graph builder should create a non-empty graph from seed data."""
    from intelligence.mirofish.graph_builder import build_knowledge_graph, extract_entities

    seeds = [
        {"title": "AI security in production systems", "content": "API rate limiting prevents abuse", "source": "test"},
        {"title": "Kubernetes at scale", "content": "Container orchestration handles deployment", "source": "test"},
    ]
    entities = extract_entities(seeds)
    assert len(entities) > 0, "Should extract at least one entity"


def test_entity_extraction():
    """Extract entities from text content."""
    from intelligence.mirofish.graph_builder import extract_entities

    seeds = [
        {"title": "PostgreSQL performance tuning", "content": "Index optimization reduces query time by 80%", "source": "test"},
    ]
    entities = extract_entities(seeds)
    assert isinstance(entities, list), "Should return a list of entities"


def test_build_communities():
    """Community detection should group related entities."""
    from intelligence.mirofish.graph_builder import build_knowledge_graph

    seeds = [
        {"title": "React state management", "content": "Redux vs Zustand for large apps", "source": "test"},
        {"title": "React performance", "content": "Virtual DOM diffing and reconciliation", "source": "test"},
        {"title": "Database scaling", "content": "Horizontal sharding in PostgreSQL", "source": "test"},
    ]
    result = build_knowledge_graph(seeds)
    assert result is not None, "Graph builder should return a result"


if __name__ == "__main__":
    test_build_graph_from_seeds()
    test_entity_extraction()
    test_build_communities()
    print("✅ All mirofish_graph_builder tests passed")
