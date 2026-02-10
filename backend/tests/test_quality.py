from app.services.quality_engine import QualityValidationEngine
from app.schemas import PillarScores

def test_validate_good_story():
    """Verify a high quality story passes validation."""
    title = "User Login"
    desc = "As a user..."
    ac = ["Given valid credentials, When I login, Then I see dashboard.", "Given invalid credentials, When I login, Then I see error."]
    
    pillars = PillarScores(
        user_value=8.0,
        commercial_impact=8.0,
        strategic_horizon=5.0,
        competitive_positioning=5.0,
        technical_reality=5.0
    )
    
    warnings = QualityValidationEngine.validate_invest(title, desc, ac, pillars)
    assert len(warnings) == 0

def test_validate_low_value_warning():
    """Verify that low value scores trigger a warning."""
    title = "Tiny Tweak"
    desc = "Change color."
    ac = ["Given x, When y, Then z."]
    
    pillars = PillarScores(
        user_value=2.0,
        commercial_impact=2.0,
        strategic_horizon=5.0,
        competitive_positioning=5.0,
        technical_reality=5.0
    )
    
    warnings = QualityValidationEngine.validate_invest(title, desc, ac, pillars)
    assert any("Low Value Warning" in w for w in warnings)

def test_validate_missing_acceptance_criteria():
    """Verify that missing AC triggers a warning."""
    title = "Missing AC"
    desc = "Do something."
    ac = []
    
    pillars = PillarScores(
        user_value=8.0,
        commercial_impact=8.0,
        strategic_horizon=5.0,
        competitive_positioning=5.0,
        technical_reality=5.0
    )
    
    warnings = QualityValidationEngine.validate_invest(title, desc, ac, pillars)
    assert any("Missing Acceptance Criteria" in w for w in warnings)
