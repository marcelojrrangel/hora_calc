from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class TimeInterval:
    start: time
    end: time

    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError("End time must be after start time")

    @property
    def duration_minutes(self) -> int:
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute
        return end_minutes - start_minutes


@dataclass(frozen=True)
class MeetingName:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Meeting name cannot be empty")
        if len(self.value) > 200:
            raise ValueError("Meeting name too long")

    @property
    def stripped(self) -> str:
        return self.value.strip()
