from datetime import time

import pytest

from app.domain.value_objects import MeetingName, TimeInterval


class TestTimeInterval:
    def test_valid_interval(self):
        interval = TimeInterval(time(9, 0), time(10, 0))
        assert interval.start == time(9, 0)
        assert interval.end == time(10, 0)

    def test_duration_60_minutes(self):
        interval = TimeInterval(time(9, 0), time(10, 0))
        assert interval.duration_minutes == 60

    def test_duration_90_minutes(self):
        interval = TimeInterval(time(9, 0), time(10, 30))
        assert interval.duration_minutes == 90

    def test_invalid_interval_raises(self):
        with pytest.raises(ValueError, match="End time must be after start time"):
            TimeInterval(time(10, 0), time(9, 0))

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError, match="End time must be after start time"):
            TimeInterval(time(9, 0), time(9, 0))

    def test_frozen(self):
        interval = TimeInterval(time(9, 0), time(10, 0))
        with pytest.raises(AttributeError):
            interval.start = time(11, 0)


class TestMeetingName:
    def test_valid_name(self):
        name = MeetingName("Daily Scrum")
        assert name.value == "Daily Scrum"

    def test_stripped(self):
        name = MeetingName("  Daily Scrum  ")
        assert name.stripped == "Daily Scrum"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            MeetingName("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            MeetingName("   ")

    def test_name_too_long_raises(self):
        with pytest.raises(ValueError, match="name too long"):
            MeetingName("x" * 201)

    def test_frozen(self):
        name = MeetingName("Daily")
        with pytest.raises(AttributeError):
            name.value = "Other"
