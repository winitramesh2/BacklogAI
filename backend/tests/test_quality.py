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

def test_validate_invest_v2_missing_metrics():
    warnings, score = QualityValidationEngine.validate_invest_v2(
        summary="Improve onboarding",
        user_story="As a user, I want faster onboarding so that I can get value quickly.",
        acceptance_criteria=[
            "Given I sign up, When I complete the onboarding flow, Then I reach the dashboard."
        ],
        dependencies=[],
        metrics=[],
        non_functional_reqs=[]
    )
    assert any("Success metrics" in w for w in warnings)
    assert score < 100


def test_evaluate_story_v2_returns_machine_readable_warnings():
    evaluation = QualityValidationEngine.evaluate_story_v2(
        summary="",
        user_story="As a user I want dashboard",
        acceptance_criteria=["When I click submit then form saves"],
        dependencies=["Analytics service", "CRM", "Identity service", "Email service"],
        metrics=[],
        non_functional_reqs=[],
        evidence_signal=0.2,
    )

    assert evaluation["quality_score"] < 100
    assert len(evaluation["warnings"]) > 0
    assert all(hasattr(w, "code") and hasattr(w, "severity") for w in evaluation["warnings"])
    assert evaluation["execution_readiness_score"] <= 100
