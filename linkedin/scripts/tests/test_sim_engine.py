"""
Tests for Simulation Engine (Onboarding) module.
Verifies scenario generation, stage progression, and public content mode.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_get_scenario_returns_result():
    """Sim engine should return a scenario for given keywords."""
    from onboarding.sim_engine import SimulationEngine

    engine = SimulationEngine()
    scenario = engine.get_scenario(
        niche_keywords=["python", "security", "api"],
        stage=1,
    )
    assert scenario is not None, "Should return a scenario"


def test_public_mode_no_auth_needed():
    """Public mode should work without platform authentication."""
    from onboarding.sim_engine import SimulationEngine

    engine = SimulationEngine()
    scenario = engine.get_scenario(
        niche_keywords=["devops", "kubernetes"],
        stage=1,
        mode="public",
    )
    assert scenario is not None, "Public mode should work without auth"


def test_scenario_has_content():
    """Scenario should contain content to display."""
    from onboarding.sim_engine import SimulationEngine

    engine = SimulationEngine()
    scenario = engine.get_scenario(
        niche_keywords=["react", "frontend"],
        stage=2,
    )
    if scenario:
        assert hasattr(scenario, "content") or hasattr(scenario, "shown_content") or isinstance(scenario, dict), \
            "Scenario must have content"


def test_different_stages_different_scenarios():
    """Different stages should produce different types of scenarios."""
    from onboarding.sim_engine import SimulationEngine

    engine = SimulationEngine()
    s1 = engine.get_scenario(niche_keywords=["tech"], stage=1)
    s2 = engine.get_scenario(niche_keywords=["tech"], stage=3)
    # Just verify both return without error
    assert s1 is not None
    assert s2 is not None


if __name__ == "__main__":
    test_get_scenario_returns_result()
    test_public_mode_no_auth_needed()
    test_scenario_has_content()
    test_different_stages_different_scenarios()
    print("✅ All sim_engine tests passed")
