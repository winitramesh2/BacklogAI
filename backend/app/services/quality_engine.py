from typing import List
from app.schemas import PillarScores

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
        warnings: List[str] = []
        score = 100.0

        if not summary or len(summary) < 5:
            warnings.append("Missing or weak summary.")
            score -= 10
        if len(summary) > 120:
            warnings.append("Summary is too long. Consider tightening the story scope.")
            score -= 5

        if "so that" not in user_story.lower():
            warnings.append("User story lacks clear value statement (missing 'so that').")
            score -= 10

        solution_terms = [
            "implement", "build", "database", "endpoint", "api", "schema", "table",
            "microservice", "backend", "frontend"
        ]
        if any(term in user_story.lower() for term in solution_terms):
            warnings.append("User story is too solution-focused. Make it more negotiable.")
            score -= 5

        if not acceptance_criteria:
            warnings.append("Missing acceptance criteria.")
            score -= 15
        elif len(acceptance_criteria) < 3:
            warnings.append("Acceptance criteria are thin. Add more scenarios.")
            score -= 8
        elif len(acceptance_criteria) > 6:
            warnings.append("Too many acceptance criteria for a single story.")
            score -= 5

        if acceptance_criteria:
            invalid_gherkin = [
                c for c in acceptance_criteria
                if "Given" not in c or "When" not in c or "Then" not in c
            ]
            if invalid_gherkin:
                warnings.append("Some acceptance criteria are not in Given/When/Then format.")
                score -= 5

        if not metrics:
            warnings.append("Success metrics are missing. Add measurable outcomes.")
            score -= 5

        if not non_functional_reqs:
            warnings.append("Non-functional requirements are missing.")
            score -= 3

        if dependencies and len(dependencies) > 3:
            warnings.append("Story has many dependencies. Consider splitting for independence.")
            score -= 5

        score = max(score, 0.0)
        return warnings, score
