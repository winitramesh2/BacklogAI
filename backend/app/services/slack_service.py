import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from app.models import SlackSession, SlackSessionStatus


class SlackService:
    def __init__(self) -> None:
        self.bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")
        self.enabled = os.getenv("SLACK_INTEGRATION_ENABLED", "false").lower() == "true"
        self.base_url = "https://slack.com/api"

    @property
    def is_configured(self) -> bool:
        return self.enabled and bool(self.bot_token) and bool(self.signing_secret)

    def verify_signature(self, timestamp: str, signature: str, body: bytes) -> bool:
        if not self.signing_secret or not timestamp or not signature:
            return False
        try:
            request_age = abs(int(time.time()) - int(timestamp))
        except ValueError:
            return False

        if request_age > 60 * 5:
            return False

        basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        digest = hmac.new(
            self.signing_secret.encode("utf-8"),
            basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        computed = f"v0={digest}"
        return hmac.compare_digest(computed, signature)

    async def _api_post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{self.base_url}/{endpoint}", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok", False):
                raise RuntimeError(f"Slack API error ({endpoint}): {data.get('error', 'unknown')}")
            return data

    async def _try_join_channel(self, channel_id: str) -> None:
        await self._api_post("conversations.join", {"channel": channel_id})

    async def _post_message_with_retry(self, channel_id: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "channel": channel_id,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks

        try:
            return await self._api_post("chat.postMessage", payload)
        except RuntimeError as exc:
            if "not_in_channel" in str(exc):
                # Works for public channels when bot has appropriate scopes.
                await self._try_join_channel(channel_id)
                return await self._api_post("chat.postMessage", payload)
            raise

    async def open_input_modal(self, trigger_id: str, channel_id: str, user_id: str) -> None:
        view = {
            "type": "modal",
            "callback_id": "backlogai_modal_submit",
            "title": {"type": "plain_text", "text": "BacklogAI"},
            "submit": {"type": "plain_text", "text": "Generate"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "private_metadata": json.dumps({"channel_id": channel_id, "user_id": user_id}),
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*BacklogAI Input Form*\nShare context and objective. We will generate a Jira-ready story preview.",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Required: *Context* and *Objective*. Optional fields improve quality and prioritization.",
                        }
                    ],
                },
                {"type": "divider"},
                self._input_block(
                    "context",
                    "Context",
                    True,
                    multiline=True,
                    placeholder="Describe product background and user problem",
                    hint="Include current pain point, affected users, and business context.",
                ),
                self._input_block(
                    "objective",
                    "Objective",
                    True,
                    multiline=True,
                    placeholder="State the desired outcome",
                    hint="Keep this outcome-focused and measurable.",
                ),
                self._input_block(
                    "target_user",
                    "Target User",
                    False,
                    placeholder="Example: Product Manager",
                    hint="Primary persona who benefits from this change.",
                ),
                self._input_block(
                    "market_segment",
                    "Market Segment",
                    False,
                    placeholder="Example: B2B SaaS",
                    hint="Industry or segment this story targets.",
                ),
                self._input_block(
                    "constraints",
                    "Constraints",
                    False,
                    multiline=True,
                    placeholder="List technical or business constraints",
                    hint="Regulatory, timeline, platform, or architecture constraints.",
                ),
                self._input_block(
                    "success_metrics",
                    "Success Metrics",
                    False,
                    multiline=True,
                    placeholder="Define measurable success outcomes",
                    hint="Examples: completion rate, SLA, reduction percentage.",
                ),
                self._input_block(
                    "competitors",
                    "Competitors (comma-separated)",
                    False,
                    placeholder="Example: Linear, Productboard",
                    hint="Optional. Used for comparative market analysis.",
                ),
            ],
        }
        await self._api_post("views.open", {"trigger_id": trigger_id, "view": view})

    @staticmethod
    def _input_block(
        action_id: str,
        label: str,
        required: bool,
        multiline: bool = False,
        placeholder: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        element = {
            "type": "plain_text_input",
            "action_id": action_id,
            "multiline": multiline,
        }
        if placeholder:
            element["placeholder"] = {"type": "plain_text", "text": placeholder}
        block: Dict[str, Any] = {
            "type": "input",
            "block_id": action_id,
            "label": {"type": "plain_text", "text": label},
            "element": element,
            "optional": not required,
        }
        if hint:
            block["hint"] = {"type": "plain_text", "text": hint}
        return block

    @staticmethod
    def parse_modal_submission(payload: Dict[str, Any]) -> Dict[str, Any]:
        state_values = payload.get("view", {}).get("state", {}).get("values", {})

        def get_value(key: str) -> str:
            block = state_values.get(key, {})
            field = block.get(key, {})
            return (field.get("value") or "").strip()

        competitors = get_value("competitors")
        competitors_list = [c.strip() for c in competitors.split(",") if c.strip()]

        return {
            "context": get_value("context"),
            "objective": get_value("objective"),
            "target_user": get_value("target_user") or None,
            "market_segment": get_value("market_segment") or None,
            "constraints": get_value("constraints") or None,
            "success_metrics": get_value("success_metrics") or None,
            "competitors_optional": competitors_list,
        }

    async def create_session(
        self,
        slack_user_id: str,
        slack_channel_id: str,
        input_payload: Dict[str, Any],
        preview_payload: Dict[str, Any],
    ) -> SlackSession:
        session = await SlackSession.create(
            slack_user_id=slack_user_id,
            slack_channel_id=slack_channel_id,
            input_payload=input_payload,
            preview_payload=preview_payload,
            status=SlackSessionStatus.GENERATED,
        )
        return session

    async def get_session(self, session_id: str) -> Optional[SlackSession]:
        return await SlackSession.filter(id=session_id).first()

    async def mark_synced(self, session: SlackSession, jira_key: str, jira_url: str) -> None:
        session.status = SlackSessionStatus.SYNCED
        session.jira_key = jira_key
        session.jira_url = jira_url
        await session.save()

    async def post_preview(
        self,
        channel_id: str,
        summary: str,
        user_story: str,
        acceptance_criteria: List[str],
        quality_score: float,
        moscow_priority: str,
        session_id: str,
    ) -> Dict[str, Any]:
        ac_lines = acceptance_criteria[:5]
        ac_text = "\n".join([f"• {line}" for line in ac_lines]) if ac_lines else "• None"
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "BacklogAI Story Preview ✨"},
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Review this draft before syncing. Generated from your Slack inputs.",
                    }
                ],
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*📝 Summary*\n{summary}"},
                    {"type": "mrkdwn", "text": f"*📌 Priority*\n{moscow_priority}"},
                    {"type": "mrkdwn", "text": f"*✅ Quality Score*\n{int(quality_score)}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*👤 User Story*\n{user_story}"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*🧪 Acceptance Criteria*\n{ac_text}"},
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🟣 *Hint:* Click *Sync to JIRA* after final review. Button color is controlled by Slack and cannot be customized to magenta.",
                    }
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "style": "primary",
                        "text": {"type": "plain_text", "text": "Sync to JIRA"},
                        "action_id": "sync_to_jira",
                        "value": session_id,
                    }
                ],
            },
        ]

        return await self._post_message_with_retry(
            channel_id=channel_id,
            text="BacklogAI Story Preview",
            blocks=blocks,
        )

    async def post_sync_success(self, channel_id: str, jira_key: str, jira_url: str) -> Dict[str, Any]:
        text = f"JIRA ticket created: *{jira_key}*\n<{jira_url}|Open ticket>"
        return await self._post_message_with_retry(channel_id=channel_id, text=text)

    async def post_error(self, channel_id: str, message: str) -> Dict[str, Any]:
        return await self._post_message_with_retry(
            channel_id=channel_id,
            text=f"BacklogAI error: {message}",
        )
