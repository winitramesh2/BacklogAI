from typing import Dict, Tuple
from app.schemas import PriorityLevel

class PrioritizationEngine:
    
    @staticmethod
    def calculate_priority(pillar_scores: Dict[str, float]) -> Tuple[float, PriorityLevel]:
        """
        Calculates a priority score (0-100) and MoSCoW category based on the 5 Pillars.
        
        Formula: Weighted Average of 5 Pillars (for simplicity) 
        OR adapted RICE: (User * Commercial * Strategic) / Effort
        
        Let's use a Weighted Score approach for robustness as specific RICE inputs (Reach/Confidence) 
        aren't directly mapped 1:1.
        
        Score = (User * 2 + Commercial * 2 + Strategic * 1.5 + Competitive * 1 + Tech * 1.5) / 8
        """
        
        # Extract scores (default to 5 if missing)
        uv = pillar_scores.get('user_value', 5.0)
        ci = pillar_scores.get('commercial_impact', 5.0)
        sh = pillar_scores.get('strategic_horizon', 5.0)
        cp = pillar_scores.get('competitive_positioning', 5.0)
        tr = pillar_scores.get('technical_reality', 5.0)
        
        # Weighted Algorithm
        # User Value & Commercial Impact are king (x2)
        # Strategic Horizon & Tech Reality are heavily influential (x1.5)
        # Competitive Positioning is a modifier (x1)
        
        weighted_sum = (uv * 2.0) + (ci * 2.0) + (sh * 1.5) + (tr * 1.5) + (cp * 1.0)
        total_weight = 2.0 + 2.0 + 1.5 + 1.5 + 1.0 # 8.0
        
        final_score = (weighted_sum / total_weight) * 10 # Scale to 0-100
        
        # MoSCoW Classification
        if final_score >= 80:
            priority = PriorityLevel.MUST_HAVE
        elif final_score >= 60:
            priority = PriorityLevel.SHOULD_HAVE
        elif final_score >= 40:
            priority = PriorityLevel.COULD_HAVE
        else:
            priority = PriorityLevel.WONT_HAVE
            
        return round(final_score, 1), priority
