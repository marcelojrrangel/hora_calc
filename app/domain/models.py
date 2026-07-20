import uuid
from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import ROUND_HALF_UP, Decimal

from app.domain.value_objects import TimeInterval


@dataclass
class Meeting:
    name: str
    start_time: time
    end_time: time
    date: datetime | None = None
    card: str | None = None
    meeting_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Meeting name cannot be empty")
        if len(self.name) > 200:
            raise ValueError("Meeting name too long")
        TimeInterval(self.start_time, self.end_time)

    @property
    def _interval(self) -> TimeInterval:
        return TimeInterval(self.start_time, self.end_time)

    @property
    def duration_minutes(self) -> int:
        return self._interval.duration_minutes

    @property
    def duration_hours(self) -> str:
        minutes = self.duration_minutes
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0 and mins > 0:
            return f"{hours}h{mins}min"
        if hours > 0:
            return f"{hours}h"
        return f"{mins}min"

    @property
    def duration_decimal(self) -> Decimal:
        minutes = self.duration_minutes
        return (Decimal(minutes) / Decimal(60)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def reschedule(self, new_start: time, new_end: time) -> None:
        TimeInterval(new_start, new_end)
        self.start_time = new_start
        self.end_time = new_end
