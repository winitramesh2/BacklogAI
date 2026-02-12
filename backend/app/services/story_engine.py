import os
import json
from typing import List, Dict, Optional
from openai import AsyncOpenAI

from app.services.market_research_service import MarketResearchService

class StoryGenerationEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.research_service = MarketResearchService()
    
    async def generate_story(
        self, 
        title: str, 
        description: str, 
        personas: List[str], 
        pillar_scores: Dict[str, float]
    ) -> Dict:
        """
        Generates a structured User Story with Acceptance Criteria.
        """
        if not self.client:
            return self._mock_generation(title, description)
            
        system_prompt = """
        You are an expert Product Manager. Your task is to transform a feature request into a high-quality User Story following the INVEST criteria.
        
        The user story must follow the format: "As a [persona], I want [goal] so that [benefit]".
        Acceptance Criteria must be in Gherkin format (Given/When/Then).
        
        You will receive input scores for 5 strategic pillars (User Value, Commercial Impact, etc.). Use these to nuance the story.
        - High User Value -> Focus heavily on usability and delight.
        - High Technical Reality -> Focus on feasibility constraints and performance.
        - High Commercial Impact -> Emphasize metrics and conversion.
        
        Output JSON format:
        {
            "user_story": "As a...",
            "acceptance_criteria": [
                "Given... When... Then...",
                "Given... When... Then..."
            ],
            "technical_notes": "Implementation details...",
            "sub_tasks": [
                {"title": "Task 1", "description": "Do X"},
                {"title": "Task 2", "description": "Do Y"}
            ]
        }
        """
        
        user_prompt = f"""
        Feature: {title}
        Description: {description}
        Target Personas: {', '.join(personas)}
        Strategic Context (0-10):
        - User Value: {pillar_scores.get('user_value')}
        - Commercial Impact: {pillar_scores.get('commercial_impact')}
        - Technical Reality: {pillar_scores.get('technical_reality')}
        
        Please break this down into a main User Story and smaller technical sub-tasks/stories if the feature is complex.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"AI Generation Error: {e}")
            return self._mock_generation(title, description)

    def _mock_generation(self, title: str, description: str) -> Dict:
        """Fallback for when OpenAI is not configured."""
        return {
            "user_story": f"As a user, I want {title.lower()} so that I can {description.lower()}.",
            "acceptance_criteria": [
                "Given I am on the dashboard, When I click the button, Then the action completes.",
                "Given the system is offline, When I try to access, Then I see an error message."
            ],
            "technical_notes": "Mock generated content. Configure OpenAI API key for real intelligence.",
            "sub_tasks": [
                {"title": "Design UI Mockups", "description": "Create screens for " + title},
                {"title": "Implement Backend API", "description": "Endpoints for " + title},
                {"title": "Unit Testing", "description": "Verify logic for " + title}
            ]
        }

    async def generate_story_v2(
        self,
        context: str,
        objective: str,
        target_user: Optional[str],
        market_segment: Optional[str],
        constraints: Optional[str],
        success_metrics: Optional[str],
        competitors: List[str],
    ) -> Dict:
        if not self.client:
            return self._mock_generation_v2(context, objective, target_user)

        research_inputs = await self.research_service.fetch_research_inputs(
            objective=objective,
            market_segment=market_segment,
            competitors=competitors,
        )

        system_prompt = """
        You are an expert Product Manager and Business Analyst.
        Your task is to turn a product context and objective into an INVEST-compliant JIRA-ready story.
        Use the market research inputs to include trends and competitive insights.

        Return JSON only in this exact schema:
        {
          "summary": "Short action-oriented summary",
          "user_story": "As a [persona], I want [goal] so that [benefit].",
          "acceptance_criteria": ["Given... When... Then..."],
          "sub_tasks": [{"title": "Task", "description": "Details"}],
          "dependencies": ["Dependency"],
          "risks": ["Risk"],
          "metrics": ["Metric"],
          "rollout_plan": ["Step"],
          "non_functional_reqs": ["NFR"],
          "research_summary": {
            "trends": ["Trend"],
            "competitor_features": ["Feature"],
            "differentiators": ["Differentiator"],
            "risks": ["Risk"],
            "sources": ["URL"]
          },
          "pillar_scores": {
            "user_value": 0,
            "commercial_impact": 0,
            "strategic_horizon": 0,
            "competitive_positioning": 0,
            "technical_reality": 0
          }
        }

        Requirements:
        - Ensure the story is small, testable, and negotiable.
        - Use 3-6 acceptance criteria in Gherkin format.
        - Keep lists concise (max 6 items each).
        - If research inputs are missing, make reasonable assumptions and say "insufficient research" in research_summary.trends.
        """

        user_prompt = f"""
        Context: {context}
        Objective: {objective}
        Target User: {target_user or "Not specified"}
        Market Segment: {market_segment or "Not specified"}
        Constraints: {constraints or "None"}
        Success Metrics: {success_metrics or "Not specified"}
        Known Competitors: {', '.join(competitors) if competitors else "Not specified"}

        Research Queries: {', '.join(research_inputs.get('queries', [])) or "None"}
        Research Snippets: {research_inputs.get('snippets', [])}
        Research Sources: {research_inputs.get('sources', [])}
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"AI Generation Error (v2): {e}")
            return self._mock_generation_v2(context, objective, target_user)

    async def revise_story_v2(self, draft: Dict, warnings: List[str]) -> Dict:
        if not self.client:
            return draft

        system_prompt = """
        You are an expert Product Manager. Revise the draft story to address the warnings.
        Keep the same JSON schema and improve INVEST compliance.
        Return JSON only.
        """

        user_prompt = f"""
        Warnings: {warnings}
        Draft JSON: {json.dumps(draft)}
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"AI Revision Error (v2): {e}")
            return draft

    def _mock_generation_v2(self, context: str, objective: str, target_user: Optional[str]) -> Dict:
        persona = target_user or "user"
        return {
            "summary": objective[:80],
            "user_story": f"As a {persona}, I want {objective.lower()} so that I can achieve the desired outcome.",
            "acceptance_criteria": [
                "Given I have access to the product, When I complete the primary flow, Then the objective is met.",
                "Given invalid inputs, When I attempt the action, Then I see a clear error message."
            ],
            "sub_tasks": [
                {"title": "Design UX flow", "description": "Define screens and interactions"},
                {"title": "Implement API changes", "description": "Add endpoints for the new flow"}
            ],
            "dependencies": [],
            "risks": ["Insufficient research"],
            "metrics": ["Adoption rate", "Task completion"],
            "rollout_plan": ["Internal QA", "Limited beta", "Full release"],
            "non_functional_reqs": ["Performance under expected load"],
            "research_summary": {
                "trends": ["insufficient research"],
                "competitor_features": [],
                "differentiators": [],
                "risks": ["insufficient research"],
                "sources": []
            },
            "pillar_scores": {
                "user_value": 5,
                "commercial_impact": 5,
                "strategic_horizon": 5,
                "competitive_positioning": 5,
                "technical_reality": 5
            }
        }
