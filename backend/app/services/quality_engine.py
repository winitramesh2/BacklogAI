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
