from dataclasses import dataclass
from datetime import date

from .AttendanceStatus import AttendanceStatus


@dataclass
class AttendanceRecord:
    attendance_id: int
    student_id: str
    session_date: date
    session_id: str
    status: AttendanceStatus
