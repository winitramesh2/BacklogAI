from app.services.prioritization_engine import PrioritizationEngine
from app.schemas import PriorityLevel

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
