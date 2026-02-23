from typing import Dict, Tuple
from app.schemas import PriorityBand, PriorityBreakdown, PriorityLevel

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

    @staticmethod
    def calculate_priority_v2(
        pillar_scores: Dict[str, float],
        user_demand_signal: float,
        competitor_pressure_signal: float,
        effort_penalty: float,
        evidence_multiplier: float,
    ) -> Tuple[float, PriorityLevel, PriorityBand, str, float, PriorityBreakdown]:
        base_score, _ = PrioritizationEngine.calculate_priority(pillar_scores)

        demand_component = max(0.0, min(1.0, user_demand_signal)) * 8.0
        competitor_component = max(0.0, min(1.0, competitor_pressure_signal)) * 7.0
        effort_component = max(0.0, min(1.0, effort_penalty)) * 12.0
        multiplier = max(0.85, min(1.15, evidence_multiplier))

        adjusted_score = (base_score + demand_component + competitor_component - effort_component) * multiplier
        final_score = round(max(0.0, min(100.0, adjusted_score)), 1)

        if final_score >= 80.0:
            priority_level = PriorityLevel.MUST_HAVE
            priority_band = PriorityBand.VERY_HIGH
            priority_text = "Very High"
        elif final_score >= 60.0:
            priority_level = PriorityLevel.SHOULD_HAVE
            priority_band = PriorityBand.HIGH
            priority_text = "High"
        elif final_score >= 40.0:
            priority_level = PriorityLevel.COULD_HAVE
            priority_band = PriorityBand.MEDIUM
            priority_text = "Medium"
        else:
            priority_level = PriorityLevel.WONT_HAVE
            priority_band = PriorityBand.LOW
            priority_text = "Low"

        confidence = round(max(0.0, min(1.0, (multiplier - 0.8) / 0.35)), 2)

        breakdown = PriorityBreakdown(
            base_pillar_score=round(base_score, 1),
            user_demand_signal=round(demand_component, 2),
            competitor_pressure_signal=round(competitor_component, 2),
            effort_penalty=round(effort_component, 2),
            evidence_multiplier=round(multiplier, 2),
            final_score=final_score,
        )

        return final_score, priority_level, priority_band, priority_text, confidence, breakdown
