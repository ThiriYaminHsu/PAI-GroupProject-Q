from dataclasses import dataclass
from datetime import datetime


@dataclass
class Alert:
    alert_id: int
    student_id: str
    alert_type: str
    reason: str
    created_at: datetime
    resolved: bool = False
