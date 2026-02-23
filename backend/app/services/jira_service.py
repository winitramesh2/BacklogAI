import os
import socket
from atlassian import Jira
from typing import Dict, Optional, Tuple, List
from urllib.parse import urlsplit, urlunsplit

from app.schemas import ResearchSummary

class JiraService:
    def __init__(self):
        self.url = self._normalize_jira_url(os.getenv("JIRA_URL"))
        self.username = os.getenv("JIRA_USERNAME")
        self.password = os.getenv("JIRA_PASSWORD") or os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "KAN") # Default project key
        
        self.jira = None
        if self.url and self.username and self.password:
            print(f"Attempting to connect to JIRA at {self.url} as {self.username}")
            try:
                is_cloud = "atlassian.net" in self.url
                self.jira = Jira(
                    url=self.url,
                    username=self.username,
                    password=self.password,
                    cloud=is_cloud
                )
                # Essential for JIRA Server/DC to bypass XSRF checks on POST requests
                self.jira.session.headers.update({"X-Atlassian-Token": "no-check"})
                print(f"JIRA client initialized successfully (Cloud: {is_cloud}).")
            except Exception as e:
                print(f"Failed to initialize JIRA client: {e}")
        else:
            print("JIRA credentials missing. Using Mock Mode.")

    @staticmethod
    def _normalize_jira_url(raw_url: Optional[str]) -> Optional[str]:
        if not raw_url:
            return raw_url

        parsed = urlsplit(raw_url)
        hostname = parsed.hostname
        if hostname not in {"host.docker.internal", "gateway.docker.internal"}:
            return raw_url

        try:
            socket.gethostbyname(hostname)
            return raw_url
        except OSError:
            auth = ""
            if parsed.username:
                auth = parsed.username
                if parsed.password:
                    auth += f":{parsed.password}"
                auth += "@"

            port = f":{parsed.port}" if parsed.port else ""
            normalized = urlunsplit(
                (parsed.scheme, f"{auth}localhost{port}", parsed.path, parsed.query, parsed.fragment)
            )
            print(
                "JIRA_URL host alias was not resolvable; "
                f"falling back from {hostname} to localhost ({normalized})."
            )
            return normalized
    
    def create_issue(self, title: str, description: str, priority: str, issue_type: str = "Story") -> Dict[str, str]:
        """
        Creates an issue in JIRA.
        Returns a dictionary with 'key' and 'url'.
        """
        if not self.jira:
            return self._mock_create_issue(title)

        try:
            # Map internal priority to JIRA priority if needed
            # For now, we pass the title/desc directly
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': title,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            mapped_priority = self._map_priority_name(priority)
            if mapped_priority:
                issue_dict['priority'] = {'name': mapped_priority}
            try:
                new_issue = self.jira.issue_create(fields=issue_dict)
            except Exception as exc:
                if "priority" in str(exc).lower() and "priority" in issue_dict:
                    issue_dict.pop("priority", None)
                    new_issue = self.jira.issue_create(fields=issue_dict)
                else:
                    raise
            
            return {
                "key": new_issue['key'],
                "url": f"{self.url}/browse/{new_issue['key']}"
            }
            
        except Exception as e:
            print(f"JIRA Create Error: {e}")
            raise e

    def create_issue_v2(
        self,
        summary: str,
        description: str,
        priority: str,
        issue_type: str = "Story",
        labels: List[str] | None = None,
        components: List[str] | None = None,
    ) -> Dict[str, str]:
        if not self.jira:
            return self._mock_create_issue(summary)

        try:
            issue_dict = {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }

            mapped_priority = self._map_priority_name(priority)
            if mapped_priority:
                issue_dict["priority"] = {"name": mapped_priority}

            if labels:
                issue_dict["labels"] = labels
            if components:
                issue_dict["components"] = [{"name": c} for c in components]

            try:
                new_issue = self.jira.issue_create(fields=issue_dict)
            except Exception as exc:
                if "priority" in str(exc).lower() and "priority" in issue_dict:
                    issue_dict.pop("priority", None)
                    new_issue = self.jira.issue_create(fields=issue_dict)
                else:
                    raise
            return {
                "key": new_issue["key"],
                "url": f"{self.url}/browse/{new_issue['key']}"
            }
        except Exception as e:
            print(f"JIRA Create Error (v2): {e}")
            raise e

    @staticmethod
    def build_description_template(
        context: str,
        objective: str,
        user_story: str,
        acceptance_criteria: List[str],
        non_functional_reqs: List[str],
        risks: List[str],
        metrics: List[str],
        rollout_plan: List[str],
        research_summary: ResearchSummary,
        dependencies: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
        open_questions: Optional[List[str]] = None,
        out_of_scope: Optional[List[str]] = None,
    ) -> str:
        def format_section(title: str, items: List[str]) -> str:
            if not items:
                return f"*{title}*\n- None"
            lines = "\n".join([f"- {item}" for item in items])
            return f"*{title}*\n{lines}"

        parts = [
            f"*Background*\n{context}",
            f"*Objective*\n{objective}",
            f"*User Story*\n{user_story}",
            format_section("Acceptance Criteria", acceptance_criteria),
            format_section("Dependencies", dependencies or []),
            format_section("Non-functional Requirements", non_functional_reqs),
            format_section("Assumptions", assumptions or []),
            format_section("Open Questions", open_questions or []),
            format_section("Out of Scope", out_of_scope or []),
            format_section("Risks", risks),
            format_section("Metrics", metrics),
            format_section("Rollout Plan", rollout_plan),
            format_section("Market Trends", research_summary.trends),
            format_section("Competitor Features", research_summary.competitor_features),
            format_section("Differentiators", research_summary.differentiators),
            format_section("Research Sources", research_summary.sources),
        ]

        return "\n\n".join(parts)

    @staticmethod
    def _map_priority_name(priority: str | None) -> str:
        if not priority:
            return "Medium"
        text = priority.strip().lower()

        if text in {"very high", "must have", "4", "p1", "highest"}:
            return "Highest"
        if text in {"high", "should have", "3", "p2"}:
            return "High"
        if text in {"medium", "could have", "2", "p3"}:
            return "Medium"
        if text in {"low", "won't have", "wont have", "1", "p4"}:
            return "Low"
        return "Medium"

    def _mock_create_issue(self, title: str) -> Dict[str, str]:
        """Simulates JIRA creation for development/testing."""
        import random
        mock_id = random.randint(100, 999)
        mock_key = f"{self.project_key}-{mock_id}"
        return {
            "key": mock_key,
            "url": f"https://mock-jira.atlassian.net/browse/{mock_key}"
        }
