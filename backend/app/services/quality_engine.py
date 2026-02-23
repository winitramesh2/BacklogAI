from typing import List, Sequence

from app.schemas import (
    PillarScores,
    QualityBreakdown,
    QualityWarning,
    RoleScores,
    WarningSeverity,
    WarningType,
)

class QualityValidationEngine:
    
    @staticmethod
    def validate_invest(
        title: str, 
        description: str, 
        acceptance_criteria: List[str],
        pillar_scores: PillarScores
    ) -> List[str]:
        """
        Validates the backlog item against INVEST criteria.
        Returns a list of warnings (empty list = PASS).
        """
        warnings = []
        
        # 1. Independent (Cannot verify via code easily without context)
        
        # 2. Negotiable (Is description concise enough?)
        if len(description) > 1000:
            warnings.append("Story description is too long (>1000 chars). Consider breaking it down.")
            
        # 3. Valuable
        if pillar_scores.user_value < 5 and pillar_scores.commercial_impact < 5:
            warnings.append("Low Value Warning: Both User Value and Commercial Impact are below 5.")
            
        # 4. Estimable (Do we have acceptance criteria?)
        if not acceptance_criteria:
            warnings.append("Missing Acceptance Criteria. This story is not estimable.")
        elif len(acceptance_criteria) < 2:
            warnings.append("Weak Acceptance Criteria. Consider adding more scenarios (Given/When/Then).")
            
        # 5. Small (Is title specific?)
        if len(title) > 100:
            warnings.append("Title is very long. Ensure this is a Story, not an Epic.")
            
        # 6. Testable (Is criteria clear?)
        # Simple heuristic: check for 'Given', 'When', 'Then' keywords
        if acceptance_criteria:
            gherkin_count = sum(1 for c in acceptance_criteria if "Given" in c or "When" in c)
            if gherkin_count < len(acceptance_criteria):
                warnings.append("Some acceptance criteria do not follow Gherkin (Given/When/Then) format.")
                
        return warnings

    @staticmethod
    def validate_invest_v2(
        summary: str,
        user_story: str,
        acceptance_criteria: List[str],
        dependencies: List[str],
        metrics: List[str],
        non_functional_reqs: List[str],
    ) -> tuple[List[str], float]:
        evaluation = QualityValidationEngine.evaluate_story_v2(
            summary=summary,
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
            dependencies=dependencies,
            metrics=metrics,
            non_functional_reqs=non_functional_reqs,
            evidence_signal=0.0,
        )
        return evaluation["warnings_text"], evaluation["quality_score"]

    @staticmethod
    def evaluate_story_v2(
        summary: str,
        user_story: str,
        acceptance_criteria: Sequence[str],
        dependencies: Sequence[str],
        metrics: Sequence[str],
        non_functional_reqs: Sequence[str],
        evidence_signal: float,
    ) -> dict:
        warnings: List[QualityWarning] = []

        clarity = 100.0
        invest = 100.0
        testability = 100.0
        measurability = 100.0
        scope = 100.0
        evidence = max(0.0, min(100.0, evidence_signal * 100.0))

        if not summary or len(summary.strip()) < 8:
            warnings.append(
                QualityWarning(
                    code="summary_missing_or_weak",
                    type=WarningType.CLARITY,
                    severity=WarningSeverity.HIGH,
                    message="Summary is missing or too weak.",
                )
            )
            clarity -= 35
        elif len(summary) > 120:
            warnings.append(
                QualityWarning(
                    code="summary_too_long",
                    type=WarningType.CLARITY,
                    severity=WarningSeverity.MEDIUM,
                    message="Summary is too long. Tighten scope.",
                )
            )
            clarity -= 15

        lower_story = user_story.lower()
        if "as a " not in lower_story or " i want " not in lower_story or " so that " not in lower_story:
            warnings.append(
                QualityWarning(
                    code="story_not_invest_format",
                    type=WarningType.INVEST,
                    severity=WarningSeverity.HIGH,
                    message="User story should follow 'As a... I want... so that...'.",
                )
            )
            invest -= 35

        solution_terms = {
            "implement", "build", "database", "endpoint", "api", "schema", "table",
            "microservice", "backend", "frontend", "refactor"
        }
        if any(term in lower_story for term in solution_terms):
            warnings.append(
                QualityWarning(
                    code="story_solution_focused",
                    type=WarningType.INVEST,
                    severity=WarningSeverity.MEDIUM,
                    message="Story appears implementation-focused; keep solution details in tasks.",
                )
            )
            invest -= 18

        ac_list = [item.strip() for item in acceptance_criteria if item and item.strip()]
        if not ac_list:
            warnings.append(
                QualityWarning(
                    code="ac_missing",
                    type=WarningType.TESTABILITY,
                    severity=WarningSeverity.HIGH,
                    message="Acceptance criteria are missing.",
                )
            )
            testability -= 45
        else:
            if len(ac_list) < 3:
                warnings.append(
                    QualityWarning(
                        code="ac_too_few",
                        type=WarningType.TESTABILITY,
                        severity=WarningSeverity.MEDIUM,
                        message="Acceptance criteria are thin. Add additional scenarios.",
                    )
                )
                testability -= 18
            if len(ac_list) > 6:
                warnings.append(
                    QualityWarning(
                        code="ac_too_many",
                        type=WarningType.SCOPE,
                        severity=WarningSeverity.LOW,
                        message="Too many acceptance criteria for one story. Consider splitting.",
                    )
                )
                scope -= 10

            invalid_gherkin = [
                ac for ac in ac_list
                if "given" not in ac.lower() or "when" not in ac.lower() or "then" not in ac.lower()
            ]
            if invalid_gherkin:
                warnings.append(
                    QualityWarning(
                        code="ac_not_gherkin",
                        type=WarningType.TESTABILITY,
                        severity=WarningSeverity.MEDIUM,
                        message="Some acceptance criteria are not in Given/When/Then format.",
                    )
                )
                testability -= 20

            if len(set(ac.lower() for ac in ac_list)) != len(ac_list):
                warnings.append(
                    QualityWarning(
                        code="ac_duplicates",
                        type=WarningType.TESTABILITY,
                        severity=WarningSeverity.LOW,
                        message="Duplicate acceptance criteria detected.",
                    )
                )
                testability -= 8

        metric_list = [item.strip() for item in metrics if item and item.strip()]
        if not metric_list:
            warnings.append(
                QualityWarning(
                    code="metrics_missing",
                    type=WarningType.MEASURABILITY,
                    severity=WarningSeverity.MEDIUM,
                    message="Success metrics are missing.",
                )
            )
            measurability -= 28
        elif len(metric_list) < 2:
            warnings.append(
                QualityWarning(
                    code="metrics_thin",
                    type=WarningType.MEASURABILITY,
                    severity=WarningSeverity.LOW,
                    message="Only one metric found. Consider adding adoption + quality metrics.",
                )
            )
            measurability -= 10

        if not non_functional_reqs:
            warnings.append(
                QualityWarning(
                    code="nfr_missing",
                    type=WarningType.NFR,
                    severity=WarningSeverity.MEDIUM,
                    message="Non-functional requirements are missing.",
                )
            )
            scope -= 12

        if dependencies and len(dependencies) > 3:
            warnings.append(
                QualityWarning(
                    code="dependencies_many",
                    type=WarningType.SCOPE,
                    severity=WarningSeverity.MEDIUM,
                    message="Story has many dependencies. Consider splitting scope.",
                )
            )
            scope -= 18

        clarity = max(0.0, min(100.0, clarity))
        invest = max(0.0, min(100.0, invest))
        testability = max(0.0, min(100.0, testability))
        measurability = max(0.0, min(100.0, measurability))
        scope = max(0.0, min(100.0, scope))
        evidence = max(0.0, min(100.0, evidence))

        quality_score = round(
            (clarity * 0.2)
            + (invest * 0.2)
            + (testability * 0.2)
            + (measurability * 0.15)
            + (scope * 0.15)
            + (evidence * 0.1),
            1,
        )

        quality_confidence = round(max(0.0, min(1.0, ((evidence / 100.0) * 0.6) + 0.4)), 2)

        role_scores = RoleScores(
            pm_clarity=round((clarity * 0.5) + (invest * 0.5), 1),
            engineering_estimability=round((scope * 0.55) + (measurability * 0.45), 1),
            qa_testability=round((testability * 0.7) + (measurability * 0.3), 1),
            architecture_nfr_readiness=round((scope * 0.6) + ((100.0 if non_functional_reqs else 55.0) * 0.4), 1),
        )

        execution_readiness_score = round(
            (role_scores.pm_clarity * 0.3)
            + (role_scores.engineering_estimability * 0.3)
            + (role_scores.qa_testability * 0.25)
            + (role_scores.architecture_nfr_readiness * 0.15),
            1,
        )

        breakdown = QualityBreakdown(
            clarity=round(clarity, 1),
            invest=round(invest, 1),
            testability=round(testability, 1),
            measurability=round(measurability, 1),
            scope=round(scope, 1),
            evidence=round(evidence, 1),
            final_score=quality_score,
        )

        return {
            "warnings": warnings,
            "warnings_text": [warning.message for warning in warnings],
            "quality_score": quality_score,
            "quality_confidence": quality_confidence,
            "quality_breakdown": breakdown,
            "role_scores": role_scores,
            "execution_readiness_score": execution_readiness_score,
        }
