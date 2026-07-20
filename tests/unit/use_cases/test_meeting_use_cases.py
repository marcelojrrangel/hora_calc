from datetime import date, time
from unittest.mock import MagicMock

import pytest

from app.domain.exceptions import InvalidMeetingDurationError, MeetingNotFoundError
from app.use_cases.meeting_use_cases import MeetingUseCases


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def use_cases(mock_repo):
    return MeetingUseCases(repository=mock_repo)


class TestRegisterMeeting:
    def test_register_success(self, use_cases, mock_repo):
        meeting = use_cases.register_meeting(
            name="Daily", start_time=time(9, 0), end_time=time(9, 15),
        )
        assert meeting.name == "Daily"
        assert meeting.duration_minutes == 15
        mock_repo.save.assert_called_once()

    def test_register_strips_name(self, use_cases, mock_repo):
        meeting = use_cases.register_meeting(
            name="  Daily  ", start_time=time(9, 0), end_time=time(9, 15),
        )
        assert meeting.name == "Daily"

    def test_register_with_card(self, use_cases, mock_repo):
        meeting = use_cases.register_meeting(
            name="Daily", start_time=time(9, 0), end_time=time(9, 15), card="CARD-1",
        )
        assert meeting.card == "CARD-1"

    def test_register_negative_duration_raises(self, use_cases, mock_repo):
        with pytest.raises(InvalidMeetingDurationError, match="End time must be after start time"):
            use_cases.register_meeting(
                name="Invalid", start_time=time(10, 0), end_time=time(9, 0),
            )

    def test_register_zero_duration_raises(self, use_cases, mock_repo):
        with pytest.raises(InvalidMeetingDurationError, match="End time must be after start time"):
            use_cases.register_meeting(
                name="Invalid", start_time=time(9, 0), end_time=time(9, 0),
            )


class TestGetMeetings:
    def test_get_today(self, use_cases, mock_repo):
        mock_repo.find_by_date.return_value = []
        result = use_cases.get_today_meetings()
        assert result == []

    def test_get_by_date(self, use_cases, mock_repo):
        mock_repo.find_by_date.return_value = []
        result = use_cases.get_meetings_by_date(date(2026, 7, 19))
        assert result == []
        mock_repo.find_by_date.assert_called_once_with(date(2026, 7, 19))


class TestTotalHours:
    def test_empty_day(self, use_cases, mock_repo):
        mock_repo.find_by_date.return_value = []
        assert use_cases.get_total_hours(date(2026, 7, 19)) == "0min"

    def test_single_meeting(self, use_cases, mock_repo, sample_meeting):
        mock_repo.find_by_date.return_value = [sample_meeting]
        assert use_cases.get_total_hours(date(2026, 7, 19)) == "15min"

    def test_multiple_meetings(self, use_cases, mock_repo, sample_meeting, another_meeting):
        mock_repo.find_by_date.return_value = [sample_meeting, another_meeting]
        assert use_cases.get_total_hours(date(2026, 7, 19)) == "2h15min"


class TestBalance:
    def test_no_meetings(self, use_cases, mock_repo):
        mock_repo.find_by_date.return_value = []
        balance = use_cases.get_balance(date(2026, 7, 19))
        assert balance["balance_minutes"] == 480
        assert not balance["is_overtime"]

    def test_partial_day(self, use_cases, mock_repo, sample_meeting):
        mock_repo.find_by_date.return_value = [sample_meeting]
        balance = use_cases.get_balance(date(2026, 7, 19))
        assert balance["balance_minutes"] == 465
        assert not balance["is_overtime"]

    def test_overtime(self, use_cases, mock_repo):
        meetings = [
            MagicMock(duration_minutes=300),
            MagicMock(duration_minutes=300),
        ]
        mock_repo.find_by_date.return_value = meetings
        balance = use_cases.get_balance(date(2026, 7, 19))
        assert balance["balance_minutes"] < 0
        assert balance["is_overtime"]


class TestUpdateMeeting:
    def test_update_success(self, use_cases, mock_repo):
        mock_repo.update_by_index.return_value = True
        meeting = use_cases.update_meeting(
            meeting_date=date(2026, 7, 19), index=0,
            name="Updated", start_time=time(9, 0), end_time=time(10, 0),
        )
        assert meeting.name == "Updated"
        assert meeting.duration_minutes == 60

    def test_update_not_found(self, use_cases, mock_repo):
        mock_repo.update_by_index.return_value = False
        with pytest.raises(MeetingNotFoundError, match="Meeting not found"):
            use_cases.update_meeting(
                meeting_date=date(2026, 7, 19), index=0,
                name="X", start_time=time(9, 0), end_time=time(10, 0),
            )

    def test_update_invalid_duration(self, use_cases, mock_repo):
        with pytest.raises(InvalidMeetingDurationError, match="End time must be after start time"):
            use_cases.update_meeting(
                meeting_date=date(2026, 7, 19), index=0,
                name="X", start_time=time(10, 0), end_time=time(9, 0),
            )


class TestDeleteMeeting:
    def test_delete_success(self, use_cases, mock_repo):
        mock_repo.delete_by_index.return_value = True
        assert use_cases.delete_meeting(date(2026, 7, 19), 0)

    def test_delete_not_found(self, use_cases, mock_repo):
        mock_repo.delete_by_index.return_value = False
        assert not use_cases.delete_meeting(date(2026, 7, 19), 0)
