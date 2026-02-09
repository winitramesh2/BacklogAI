import os
from atlassian import Jira
from typing import Dict, Optional, Tuple

class JiraService:
    def __init__(self):
        self.url = os.getenv("JIRA_URL")
        self.username = os.getenv("JIRA_USERNAME")
        self.token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "KAN") # Default project key
        
        self.jira = None
        if self.url and self.username and self.token:
            try:
                self.jira = Jira(
                    url=self.url,
                    username=self.username,
                    password=self.token,
                    cloud=True
                )
            except Exception as e:
                print(f"Failed to initialize JIRA client: {e}")
    
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
                # Add priority if your JIRA project supports it and you know the mapping
                # 'priority': {'name': 'Medium'} 
            }

            new_issue = self.jira.issue_create(fields=issue_dict)
            
            return {
                "key": new_issue['key'],
                "url": f"{self.url}/browse/{new_issue['key']}"
            }
            
        except Exception as e:
            print(f"JIRA Create Error: {e}")
            raise e

    def _mock_create_issue(self, title: str) -> Dict[str, str]:
        """Simulates JIRA creation for development/testing."""
        import random
        mock_id = random.randint(100, 999)
        mock_key = f"{self.project_key}-{mock_id}"
        return {
            "key": mock_key,
            "url": f"https://mock-jira.atlassian.net/browse/{mock_key}"
        }
