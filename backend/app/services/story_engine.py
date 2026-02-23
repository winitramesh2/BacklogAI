import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.schemas import MetricItem
from app.services.market_research_service import MarketResearchService


class _StoryDraftV2(BaseModel):
    summary: str = ""
    user_story: str = ""
    acceptance_criteria: List[str] = Field(default_factory=list)
    sub_tasks: List[Dict[str, str]] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    metrics: List[Any] = Field(default_factory=list)
    structured_metrics: List[Any] = Field(default_factory=list)
    rollout_plan: List[str] = Field(default_factory=list)
    non_functional_reqs: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    confidence: float = 0.65
    research_summary: Dict[str, Any] = Field(default_factory=dict)
    pillar_scores: Dict[str, float] = Field(default_factory=dict)


class StoryGenerationEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.draft_model = os.getenv("OPENAI_DRAFT_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o"))
        self.revise_model = os.getenv("OPENAI_REVISE_MODEL", self.draft_model)
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
        self.timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_S", "45"))
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=self.timeout_seconds) if self.api_key else None
        self.research_service = MarketResearchService()

    @staticmethod
    def _dedupe_preserve(values: Sequence[str]) -> List[str]:
        seen = set()
        output: List[str] = []
        for item in values:
            key = item.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            output.append(item.strip())
        return output

    @classmethod
    def _sanitize_list(cls, values: Sequence[str], max_items: int = 6) -> List[str]:
        cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
        return cls._dedupe_preserve(cleaned)[:max_items]

    @staticmethod
    def _normalize_gherkin(line: str) -> str:
        text = line.strip()
        if not text:
            return text

        replacements = {
            "given": "Given",
            "when": "When",
            "then": "Then",
            "and": "And",
        }
        words = text.split()
        normalized: List[str] = []
        for word in words:
            raw = word.strip()
            lower = raw.lower().strip(".,:;")
            if lower in replacements:
                normalized.append(raw.replace(raw.strip(".,:;"), replacements[lower]))
            else:
                normalized.append(raw)
        text = " ".join(normalized)
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        return text

    @classmethod
    def _sanitize_acceptance_criteria(cls, criteria: Sequence[str]) -> List[str]:
        return [cls._normalize_gherkin(item) for item in cls._sanitize_list(criteria, max_items=6)]

    @classmethod
    def _sanitize_sub_tasks(cls, sub_tasks: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
        cleaned: List[Dict[str, str]] = []
        for entry in sub_tasks:
            if not isinstance(entry, dict):
                continue
            title = str(entry.get("title", "")).strip()
            description = str(entry.get("description", "")).strip()
            if not title:
                continue
            cleaned.append({"title": title[:120], "description": description[:400]})
        # dedupe by title
        deduped: List[Dict[str, str]] = []
        seen = set()
        for item in cleaned:
            key = item["title"].lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped[:8]

    @staticmethod
    def _metric_to_text(metric: MetricItem) -> str:
        segments = [metric.name]
        if metric.target:
            segments.append(f"target {metric.target}")
        if metric.timeframe:
            segments.append(f"within {metric.timeframe}")
        return " - ".join(segments)

    @classmethod
    def _sanitize_metrics(
        cls,
        metrics: Sequence[Any],
        structured_metrics: Sequence[Any],
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        metric_text: List[str] = []
        metric_items: List[MetricItem] = []

        merged = list(metrics) + list(structured_metrics)
        for item in merged:
            if isinstance(item, str) and item.strip():
                metric_text.append(item.strip())
                continue
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                metric = MetricItem(
                    name=name,
                    baseline=str(item.get("baseline")).strip() if item.get("baseline") else None,
                    target=str(item.get("target")).strip() if item.get("target") else None,
                    timeframe=str(item.get("timeframe")).strip() if item.get("timeframe") else None,
                    owner=str(item.get("owner")).strip() if item.get("owner") else None,
                )
                metric_items.append(metric)
                metric_text.append(cls._metric_to_text(metric))

        metric_text = cls._sanitize_list(metric_text, max_items=8)

        deduped_structured: List[Dict[str, Any]] = []
        seen = set()
        for metric in metric_items:
            key = metric.name.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped_structured.append(metric.model_dump())

        return metric_text, deduped_structured[:8]

    @staticmethod
    def _sanitize_pillar_scores(raw_scores: Dict[str, Any]) -> Dict[str, float]:
        defaults = {
            "user_value": 5.0,
            "commercial_impact": 5.0,
            "strategic_horizon": 5.0,
            "competitive_positioning": 5.0,
            "technical_reality": 5.0,
        }
        for key in defaults:
            value = raw_scores.get(key) if isinstance(raw_scores, dict) else None
            if value is None:
                continue
            try:
                defaults[key] = max(0.0, min(10.0, float(value)))
            except (TypeError, ValueError):
                continue
        return defaults

    @staticmethod
    def _tokenize(value: str) -> set[str]:
        return {word.strip(".,:;!?()[]{}\"'").lower() for word in value.split() if len(word) > 3}

    @classmethod
    def _build_citation_map(cls, research_summary: Dict[str, List[str]], source_details: Sequence[Dict[str, Any]]) -> Dict[str, List[int]]:
        citation_map: Dict[str, List[int]] = {}
        if not source_details:
            return citation_map

        source_tokens: List[Tuple[int, set[str]]] = []
        for source in source_details:
            source_id = int(source.get("id", 0))
            text = " ".join([
                str(source.get("title") or ""),
                str(source.get("snippet") or ""),
                str(source.get("domain") or ""),
            ]).strip()
            source_tokens.append((source_id, cls._tokenize(text)))

        for section in ("trends", "competitor_features", "differentiators", "risks"):
            claims = research_summary.get(section, [])
            if not isinstance(claims, list):
                continue
            for idx, claim in enumerate(claims):
                claim_tokens = cls._tokenize(str(claim))
                if not claim_tokens:
                    continue
                matched: List[int] = []
                for source_id, tokens in source_tokens:
                    overlap = len(claim_tokens.intersection(tokens))
                    if overlap >= 2:
                        matched.append(source_id)
                if matched:
                    citation_map[f"{section}:{idx}"] = matched[:3]

        return citation_map

    @classmethod
    def _sanitize_research_summary(
        cls,
        raw_summary: Dict[str, Any],
        research_inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        trends = cls._sanitize_list(raw_summary.get("trends", []), max_items=6)
        competitor_features = cls._sanitize_list(raw_summary.get("competitor_features", []), max_items=6)
        differentiators = cls._sanitize_list(raw_summary.get("differentiators", []), max_items=6)
        risks = cls._sanitize_list(raw_summary.get("risks", []), max_items=6)

        source_details = research_inputs.get("source_details", [])
        sources = research_inputs.get("sources", [])

        summary = {
            "trends": trends,
            "competitor_features": competitor_features,
            "differentiators": differentiators,
            "risks": risks,
            "sources": cls._sanitize_list(sources, max_items=12),
            "source_details": source_details[:12] if isinstance(source_details, list) else [],
        }

        citation_map = cls._build_citation_map(summary, summary["source_details"])
        claim_total = sum(len(summary.get(section, [])) for section in ("trends", "competitor_features", "differentiators", "risks"))
        mapped_claims = len(citation_map)

        quality = dict(research_inputs.get("quality", {})) if isinstance(research_inputs.get("quality"), dict) else {}
        quality["source_count"] = len(summary["source_details"])
        quality["unique_domain_count"] = len({d.get("domain") for d in summary["source_details"] if d.get("domain")})
        quality["citation_coverage"] = round(mapped_claims / claim_total, 2) if claim_total else 0.0
        quality.setdefault("freshness_coverage", 0.0)

        summary["citation_map"] = citation_map
        summary["quality"] = quality
        return summary

    @classmethod
    def _safe_merge_revision(cls, draft: Dict[str, Any], revised: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(draft)
        merged.update(revised)

        critical_fields = [
            "research_summary",
            "pillar_scores",
            "dependencies",
            "metrics",
            "structured_metrics",
            "acceptance_criteria",
            "non_functional_reqs",
        ]
        for key in critical_fields:
            revised_value = revised.get(key)
            if revised_value in (None, "", [], {}):
                merged[key] = draft.get(key)
        return merged

    @classmethod
    def _validate_and_sanitize_v2(cls, payload: Dict[str, Any], research_inputs: Dict[str, Any]) -> Dict[str, Any]:
        draft = _StoryDraftV2.model_validate(payload)

        metrics, structured_metrics = cls._sanitize_metrics(
            metrics=draft.metrics,
            structured_metrics=draft.structured_metrics,
        )
        acceptance_criteria = cls._sanitize_acceptance_criteria(draft.acceptance_criteria)

        story = {
            "summary": draft.summary.strip()[:160],
            "user_story": draft.user_story.strip(),
            "acceptance_criteria": acceptance_criteria,
            "sub_tasks": cls._sanitize_sub_tasks(draft.sub_tasks),
            "dependencies": cls._sanitize_list(draft.dependencies, max_items=6),
            "risks": cls._sanitize_list(draft.risks, max_items=6),
            "metrics": metrics,
            "structured_metrics": structured_metrics,
            "rollout_plan": cls._sanitize_list(draft.rollout_plan, max_items=6),
            "non_functional_reqs": cls._sanitize_list(draft.non_functional_reqs, max_items=6),
            "assumptions": cls._sanitize_list(draft.assumptions, max_items=5),
            "open_questions": cls._sanitize_list(draft.open_questions, max_items=5),
            "out_of_scope": cls._sanitize_list(draft.out_of_scope, max_items=5),
            "confidence": round(max(0.0, min(1.0, float(draft.confidence))), 2),
            "research_summary": cls._sanitize_research_summary(draft.research_summary, research_inputs),
            "pillar_scores": cls._sanitize_pillar_scores(draft.pillar_scores),
        }

        if not story["summary"]:
            story["summary"] = "Story draft"
        if not story["user_story"]:
            story["user_story"] = "As a user, I want this capability so that I can achieve the desired outcome."

        if not story["acceptance_criteria"]:
            story["acceptance_criteria"] = [
                "Given the user accesses the feature, When the primary flow is executed, Then the expected outcome is achieved.",
                "Given invalid input, When the user submits the request, Then a clear validation message is shown.",
                "Given a system error occurs, When the operation fails, Then the user receives an actionable error message.",
            ]

        if not story["metrics"]:
            story["metrics"] = ["Feature adoption rate", "Task completion rate"]

        if not story["rollout_plan"]:
            story["rollout_plan"] = ["Internal QA", "Pilot release", "General availability"]

        if not story["assumptions"]:
            story["assumptions"] = ["Core user journey remains unchanged outside this story scope"]

        return story

    async def _call_openai_json(self, system_prompt: str, user_prompt: str, model: str) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI client is not configured")

        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or "{}"
                return json.loads(content)
            except Exception:
                if attempt > self.max_retries:
                    raise

    async def generate_story(
        self,
        title: str,
        description: str,
        personas: List[str],
        pillar_scores: Dict[str, float],
    ) -> Dict:
        if not self.client:
            return self._mock_generation(title, description)

        system_prompt = """
        You are an expert Product Manager. Transform the feature request into a high-quality user story.
        Return JSON with: user_story, acceptance_criteria, technical_notes, sub_tasks.
        """

        user_prompt = f"""
        Feature: {title}
        Description: {description}
        Target Personas: {', '.join(personas)}
        Strategic Context (0-10): {pillar_scores}
        """

        try:
            content = await self._call_openai_json(system_prompt, user_prompt, self.draft_model)
            return {
                "user_story": str(content.get("user_story", "")).strip() or f"As a user, I want {title.lower()} so that I can achieve the objective.",
                "acceptance_criteria": self._sanitize_acceptance_criteria(content.get("acceptance_criteria", [])),
                "technical_notes": str(content.get("technical_notes", "")).strip(),
                "sub_tasks": self._sanitize_sub_tasks(content.get("sub_tasks", [])),
            }
        except Exception:
            return self._mock_generation(title, description)

    def _mock_generation(self, title: str, description: str) -> Dict:
        return {
            "user_story": f"As a user, I want {title.lower()} so that I can {description.lower()}.",
            "acceptance_criteria": [
                "Given I am on the dashboard, When I click the button, Then the action completes.",
                "Given the system is offline, When I try to access, Then I see an error message.",
            ],
            "technical_notes": "Mock generated content. Configure OpenAI API key for real intelligence.",
            "sub_tasks": [
                {"title": "Design UI Mockups", "description": "Create screens for the feature"},
                {"title": "Implement Backend API", "description": "Build required endpoints"},
                {"title": "Unit Testing", "description": "Verify core logic"},
            ],
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
        research_inputs = await self.research_service.fetch_research_inputs(
            objective=objective,
            market_segment=market_segment,
            competitors=competitors,
        )

        if not self.client:
            fallback = self._fallback_generation_v2(
                context=context,
                objective=objective,
                target_user=target_user,
                constraints=constraints,
                success_metrics=success_metrics,
                research_inputs=research_inputs,
            )
            fallback["_meta"] = {
                "used_fallback": True,
                "model_draft": self.draft_model,
                "model_revise": self.revise_model,
                "research_queries": len(research_inputs.get("queries", [])),
                "research_snippets": len(research_inputs.get("snippets", [])),
                "research_sources": len(research_inputs.get("sources", [])),
            }
            return fallback

        system_prompt = """
        You are an expert Product Manager and Business Analyst.
        Transform context + objective into an INVEST-compliant, JIRA-ready story.
        Use provided market research to ground insights.

        Return JSON only with fields:
        summary, user_story, acceptance_criteria, sub_tasks, dependencies, risks,
        metrics, structured_metrics, rollout_plan, non_functional_reqs,
        assumptions, open_questions, out_of_scope, confidence,
        research_summary {trends, competitor_features, differentiators, risks},
        pillar_scores {user_value, commercial_impact, strategic_horizon, competitive_positioning, technical_reality}

        Rules:
        - 3-6 acceptance criteria, Given/When/Then
        - concise lists, max 6 each
        - avoid implementation detail in user_story
        - confidence must be 0..1
        """

        user_prompt = f"""
        Context: {context}
        Objective: {objective}
        Target User: {target_user or "Not specified"}
        Market Segment: {market_segment or "Not specified"}
        Constraints: {constraints or "None"}
        Success Metrics: {success_metrics or "Not specified"}
        Known Competitors: {', '.join(competitors) if competitors else "Not specified"}

        Research Queries: {', '.join(research_inputs.get('queries', [])) or 'None'}
        Research Snippets: {research_inputs.get('snippets', [])}
        Research Sources: {research_inputs.get('sources', [])}
        """

        try:
            payload = await self._call_openai_json(system_prompt, user_prompt, self.draft_model)
            story = self._validate_and_sanitize_v2(payload, research_inputs)
            story["_meta"] = {
                "used_fallback": False,
                "model_draft": self.draft_model,
                "model_revise": self.revise_model,
                "research_queries": len(research_inputs.get("queries", [])),
                "research_snippets": len(research_inputs.get("snippets", [])),
                "research_sources": len(research_inputs.get("sources", [])),
            }
            return story
        except Exception:
            fallback = self._fallback_generation_v2(
                context=context,
                objective=objective,
                target_user=target_user,
                constraints=constraints,
                success_metrics=success_metrics,
                research_inputs=research_inputs,
            )
            fallback["_meta"] = {
                "used_fallback": True,
                "model_draft": self.draft_model,
                "model_revise": self.revise_model,
                "research_queries": len(research_inputs.get("queries", [])),
                "research_snippets": len(research_inputs.get("snippets", [])),
                "research_sources": len(research_inputs.get("sources", [])),
            }
            return fallback

    async def revise_story_v2(self, draft: Dict, warnings: List[str]) -> Dict:
        if not self.client:
            return draft

        system_prompt = """
        You are an expert Product Manager.
        Revise the draft story to resolve warnings while preserving original intent and schema.
        Return JSON only.
        """
        user_prompt = f"Warnings: {warnings}\nDraft JSON: {json.dumps(draft)}"

        research_summary = draft.get("research_summary", {}) if isinstance(draft, dict) else {}
        research_inputs = {
            "sources": research_summary.get("sources", []),
            "source_details": research_summary.get("source_details", []),
            "quality": research_summary.get("quality", {}),
        }

        try:
            revised_payload = await self._call_openai_json(system_prompt, user_prompt, self.revise_model)
            revised_story = self._validate_and_sanitize_v2(revised_payload, research_inputs)
            merged = self._safe_merge_revision(draft, revised_story)
            if "_meta" in draft:
                merged["_meta"] = draft["_meta"]
            return merged
        except Exception:
            return draft

    def _fallback_generation_v2(
        self,
        context: str,
        objective: str,
        target_user: Optional[str],
        constraints: Optional[str],
        success_metrics: Optional[str],
        research_inputs: Dict,
    ) -> Dict:
        persona = target_user or "user"
        metrics = self._split_list(success_metrics)
        non_functional = self._split_list(constraints)

        raw_summary = {
            "trends": research_inputs.get("snippets", [])[:4] or ["insufficient research"],
            "competitor_features": [],
            "differentiators": [],
            "risks": ["insufficient research"],
        }
        research_summary = self._sanitize_research_summary(raw_summary, research_inputs)

        return {
            "summary": objective[:120],
            "user_story": f"As a {persona}, I want {objective.lower()} so that I can achieve the desired outcome.",
            "acceptance_criteria": [
                "Given I have access to the product, When I complete the primary flow, Then the objective is met.",
                "Given invalid inputs, When I attempt the action, Then I see a clear error message.",
                "Given a temporary system issue, When the operation fails, Then the user receives a retry path.",
            ],
            "sub_tasks": [
                {"title": "Design UX flow", "description": "Define screens and interactions"},
                {"title": "Implement API changes", "description": "Add endpoints for the new flow"},
            ],
            "dependencies": [],
            "risks": ["Insufficient research"],
            "metrics": metrics or ["Adoption rate", "Task completion rate"],
            "structured_metrics": [],
            "rollout_plan": ["Internal QA", "Limited beta", "General availability"],
            "non_functional_reqs": non_functional or ["Performance under expected load"],
            "assumptions": ["Existing user permissions model remains unchanged"],
            "open_questions": ["Define release success threshold with PM and engineering"],
            "out_of_scope": ["Major redesign outside the current objective scope"],
            "confidence": 0.55,
            "research_summary": research_summary,
            "pillar_scores": {
                "user_value": 5,
                "commercial_impact": 5,
                "strategic_horizon": 5,
                "competitive_positioning": 5,
                "technical_reality": 5,
            },
        }

    @staticmethod
    def _split_list(value: Optional[str]) -> List[str]:
        if not value:
            return []
        parts = [p.strip() for p in value.replace(";", ",").split(",")]
        return [p for p in parts if p]
