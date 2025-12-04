from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuditLog:
    log_id: int
    user_id: int
    entitiy_type: str
    entity_id: int
    action_type: str
    timestamp: datetime
    details: str = ""
