from datetime import date, time
from decimal import Decimal

import pytest

from app.domain.models import Meeting


class TestMeetingCreation:
    def test_minimal_meeting(self):
        meeting = Meeting(name="Daily", start_time=time(9, 0), end_time=time(9, 15))
        assert meeting.name == "Daily"
        assert meeting.start_time == time(9, 0)
        assert meeting.end_time == time(9, 15)
        assert meeting.date is None
        assert meeting.card is None

    def test_full_meeting(self, sample_meeting):
        assert sample_meeting.name == "Daily Scrum"
        assert sample_meeting.date == date(2026, 7, 19)
        assert sample_meeting.card is None

    def test_meeting_with_card(self, another_meeting):
        assert another_meeting.card == "CARD-123"

    def test_name_with_whitespace(self):
        meeting = Meeting(name="  Meeting  ", start_time=time(9, 0), end_time=time(10, 0))
        assert meeting.name == "  Meeting  "

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Meeting(name="", start_time=time(9, 0), end_time=time(10, 0))

    def test_whitespace_only_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Meeting(name="   ", start_time=time(9, 0), end_time=time(10, 0))

    def test_name_too_long_raises(self):
        with pytest.raises(ValueError, match="name too long"):
            Meeting(name="x" * 201, start_time=time(9, 0), end_time=time(10, 0))

    def test_invalid_duration_raises(self):
        with pytest.raises(ValueError, match="End time must be after start time"):
            Meeting(name="Test", start_time=time(10, 0), end_time=time(9, 0))

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError, match="End time must be after start time"):
            Meeting(name="Test", start_time=time(9, 0), end_time=time(9, 0))


class TestMeetingDuration:
    def test_15_minutes(self, sample_meeting):
        assert sample_meeting.duration_minutes == 15

    def test_2_hours(self, another_meeting):
        assert another_meeting.duration_minutes == 120

    def test_exact_one_hour(self):
        meeting = Meeting(name="Test", start_time=time(8, 0), end_time=time(9, 0))
        assert meeting.duration_minutes == 60


class TestDurationHours:
    def test_hours_and_minutes(self):
        m = Meeting(name="T", start_time=time(8, 0), end_time=time(10, 30))
        assert m.duration_hours == "2h30min"

    def test_only_hours(self):
        m = Meeting(name="T", start_time=time(8, 0), end_time=time(12, 0))
        assert m.duration_hours == "4h"

    def test_only_minutes(self):
        m = Meeting(name="T", start_time=time(9, 0), end_time=time(9, 45))
        assert m.duration_hours == "45min"


class TestDurationDecimal:
    def test_exact_hour(self):
        m = Meeting(name="T", start_time=time(8, 0), end_time=time(9, 0))
        assert m.duration_decimal == Decimal("1.00")

    def test_half_hour(self):
        m = Meeting(name="T", start_time=time(8, 0), end_time=time(8, 30))
        assert m.duration_decimal == Decimal("0.50")

    def test_15_minutes(self):
        m = Meeting(name="T", start_time=time(8, 0), end_time=time(8, 15))
        assert m.duration_decimal == Decimal("0.25")

    def test_rounding(self):
        m = Meeting(name="T", start_time=time(8, 0), end_time=time(8, 10))
        assert m.duration_decimal == Decimal("0.17")


class TestReschedule:
    def test_reschedule_success(self):
        meeting = Meeting(name="Test", start_time=time(9, 0), end_time=time(10, 0))
        meeting.reschedule(time(11, 0), time(12, 0))
        assert meeting.start_time == time(11, 0)
        assert meeting.end_time == time(12, 0)
        assert meeting.duration_minutes == 60

    def test_reschedule_invalid_raises(self):
        meeting = Meeting(name="Test", start_time=time(9, 0), end_time=time(10, 0))
        with pytest.raises(ValueError, match="End time must be after start time"):
            meeting.reschedule(time(12, 0), time(11, 0))
