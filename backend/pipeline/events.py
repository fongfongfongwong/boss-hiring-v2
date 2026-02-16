"""WebSocket event types for real-time progress updates."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class PipelineEvent:
    """An event emitted by the pipeline to be sent over WebSocket."""

    event_type: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Event type constants
TASK_STARTED = "task_started"
TASK_PAUSED = "task_paused"
TASK_RESUMED = "task_resumed"
TASK_COMPLETED = "task_completed"
TASK_FAILED = "task_failed"

STEP1_START = "step1_analyzing_position"
STEP1_DONE = "step1_position_analyzed"

STEP2_START = "step2_launching_browser"
STEP2_DONE = "step2_browser_ready"

STEP3_SEARCHING = "step3_searching_candidates"
STEP3_CANDIDATE_FOUND = "step3_candidate_found"
STEP3_GREETING_SENT = "step3_greeting_sent"
STEP3_REPLY_RECEIVED = "step3_reply_received"
STEP3_RESUME_RECEIVED = "step3_resume_received"

STEP4_SCORING = "step4_scoring_resume"
STEP4_SCORED = "step4_resume_scored"

STEP5_CONTACT_REQUEST = "step5_requesting_contact"
STEP5_CONTACT_OBTAINED = "step5_contact_obtained"

PROGRESS_UPDATE = "progress_update"
WARNING = "warning"
ERROR = "error"
