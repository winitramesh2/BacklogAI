from tortoise import fields, models
from enum import Enum
from uuid import uuid4

class User(models.Model):
    id = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    full_name = fields.CharField(max_length=255, null=True)
    picture = fields.CharField(max_length=1024, null=True)
    auth_provider = fields.CharField(max_length=50, default="google") # google, github
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

class Project(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    owner = fields.ForeignKeyField("models.User", related_name="projects")
    
    # Configuration for the 5 Pillars (Weights 0.0 - 1.0)
    # Default is equal weight (0.2 each)
    weight_user_value = fields.FloatField(default=0.2)
    weight_commercial_impact = fields.FloatField(default=0.2)
    weight_strategic_horizon = fields.FloatField(default=0.2)
    weight_competitive_positioning = fields.FloatField(default=0.2)
    weight_technical_reality = fields.FloatField(default=0.2)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "projects"

class BacklogItemType(str, Enum):
    EPIC = "epic"
    STORY = "story"
    TASK = "task"

class BacklogItemStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SYNCED = "synced"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class BacklogItem(models.Model):
    id = fields.UUIDField(pk=True)
    project = fields.ForeignKeyField("models.Project", related_name="backlog_items")
    parent = fields.ForeignKeyField("models.BacklogItem", related_name="children", null=True)
    
    type = fields.CharEnumField(BacklogItemType, default=BacklogItemType.STORY)
    status = fields.CharEnumField(BacklogItemStatus, default=BacklogItemStatus.DRAFT)
    
    title = fields.CharField(max_length=255)
    description = fields.TextField() # As a... I want... So that...
    acceptance_criteria = fields.JSONField(default=list) # List of Given/When/Then strings
    
    # Calculated Scores
    priority_score = fields.FloatField(default=0.0)
    
    # 5 Pillar Scores (0-10)
    score_user_value = fields.FloatField(default=0.0)
    score_commercial_impact = fields.FloatField(default=0.0)
    score_strategic_horizon = fields.FloatField(default=0.0)
    score_competitive_positioning = fields.FloatField(default=0.0)
    score_technical_reality = fields.FloatField(default=0.0)
    
    # JIRA Integration
    jira_key = fields.CharField(max_length=50, null=True)
    jira_url = fields.CharField(max_length=512, null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "backlog_items"


class SlackSessionStatus(str, Enum):
    GENERATED = "generated"
    SYNCED = "synced"
    EXPIRED = "expired"


class SlackSession(models.Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    slack_user_id = fields.CharField(max_length=64)
    slack_channel_id = fields.CharField(max_length=64)
    slack_message_ts = fields.CharField(max_length=64, null=True)
    input_payload = fields.JSONField(default=dict)
    preview_payload = fields.JSONField(default=dict)
    status = fields.CharEnumField(SlackSessionStatus, default=SlackSessionStatus.GENERATED)
    jira_key = fields.CharField(max_length=50, null=True)
    jira_url = fields.CharField(max_length=512, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "slack_sessions"
