from app.services.prioritization_engine import PrioritizationEngine
from app.schemas import PriorityBand, PriorityLevel

def test_must_have_calculation():
    """Verify that high scores result in MUST_HAVE."""
    pillar_scores = {
        'user_value': 9.0,
        'commercial_impact': 9.0,
        'strategic_horizon': 9.0,
        'competitive_positioning': 9.0,
        'technical_reality': 9.0
    }
    
    score, priority = PrioritizationEngine.calculate_priority(pillar_scores)
    
    assert score >= 80.0
    assert priority == PriorityLevel.MUST_HAVE

def test_wont_have_calculation():
    """Verify that low scores result in WONT_HAVE."""
    pillar_scores = {
        'user_value': 1.0,
        'commercial_impact': 1.0,
        'strategic_horizon': 1.0,
        'competitive_positioning': 1.0,
        'technical_reality': 1.0
    }
    
    score, priority = PrioritizationEngine.calculate_priority(pillar_scores)
    
    assert score < 40.0
    assert priority == PriorityLevel.WONT_HAVE

def test_edge_cases_default_values():
    """Verify default values (5.0) are used correctly."""
    pillar_scores = {} # Empty
    
    score, priority = PrioritizationEngine.calculate_priority(pillar_scores)
    
    # 5.0 across the board -> 50.0 score -> COULD_HAVE
    assert score == 50.0
    assert priority == PriorityLevel.COULD_HAVE


def test_priority_v2_includes_signals_and_label():
    pillar_scores = {
        "user_value": 8.0,
        "commercial_impact": 8.0,
        "strategic_horizon": 7.0,
        "competitive_positioning": 7.0,
        "technical_reality": 6.0,
    }

    score, priority_level, priority_band, label, confidence, breakdown = PrioritizationEngine.calculate_priority_v2(
        pillar_scores=pillar_scores,
        user_demand_signal=0.8,
        competitor_pressure_signal=0.7,
        effort_penalty=0.2,
        evidence_multiplier=1.05,
    )

    assert score > 60.0
    assert priority_level in {PriorityLevel.SHOULD_HAVE, PriorityLevel.MUST_HAVE}
    assert priority_band in {PriorityBand.HIGH, PriorityBand.VERY_HIGH}
    assert label in {"High", "Very High"}
    assert 0.0 <= confidence <= 1.0
    assert breakdown.final_score == score
