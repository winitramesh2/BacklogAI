import os
import json
from typing import List, Dict, Optional
from openai import AsyncOpenAI

class StoryGenerationEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
    
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
