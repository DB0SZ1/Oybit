"""
MiroFish Report Agent — Agent A Module
Synthesizes simulation results into structured narrative prediction output.
"""

from dataclasses import dataclass, field, asdict
import json


@dataclass
class NarrativePrediction:
    topic: str
    relevance_to_persona: float
    predicted_peak: str
    framing_suggestion: str
    resonant_angles: list = field(default_factory=list)
    avoid_angles: list = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ForecastReport:
    rising_narratives: list = field(default_factory=list)
    timing_recommendations: dict = field(default_factory=dict)
    narrative_forecast_72h: str = ""
    avoid_posting_now: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "rising_narratives": [asdict(n) for n in self.rising_narratives],
            "timing_recommendations": self.timing_recommendations,
            "narrative_forecast_72h": self.narrative_forecast_72h,
            "avoid_posting_now": self.avoid_posting_now,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def synthesize_report(simulation_results: dict = None, graph_data=None) -> ForecastReport:
    """Synthesize simulation results into a forecast report."""
    report = ForecastReport(
        timing_recommendations={
            "linkedin": "08:00-10:00 WAT",
            "instagram_personal": "19:00-21:00 WAT",
            "instagram_brand": "12:00-14:00 WAT",
            "facebook": "18:00-20:00 WAT",
        },
        narrative_forecast_72h="Monitor emerging developer tool security and AI integration trends.",
        avoid_posting_now=["general AI hype", "cryptocurrency", "generic productivity tips"],
    )
    
    if simulation_results and isinstance(simulation_results, dict):
        narratives = simulation_results.get("narratives", [])
        for n in narratives:
            report.rising_narratives.append(NarrativePrediction(
                topic=n.get("topic", ""),
                relevance_to_persona=n.get("relevance", 0.0),
                predicted_peak=n.get("peak", ""),
                framing_suggestion=n.get("framing", ""),
                resonant_angles=n.get("resonant_angles", []),
                avoid_angles=n.get("avoid_angles", []),
                confidence=n.get("confidence", 0.0),
            ))
    
    return report
