import logging
from datetime import date, time

from app.config import settings
from app.domain.exceptions import InvalidMeetingDurationError, MeetingNotFoundError
from app.domain.models import Meeting
from app.domain.repositories import MeetingRepository

logger = logging.getLogger(__name__)


class MeetingUseCases:
    def __init__(self, repository: MeetingRepository):
        self._repository = repository

    def register_meeting(
        self, name: str, start_time: time, end_time: time,
        meeting_date: date | None = None, card: str | None = None,
    ) -> Meeting:
        try:
            meeting = Meeting(
                name=name.strip(),
                start_time=start_time,
                end_time=end_time,
                date=meeting_date,
                card=card,
            )
        except ValueError as e:
            if "End time" in str(e):
                raise InvalidMeetingDurationError(str(e))
            raise
        self._repository.save(meeting)
        logger.info(
            "Meeting registered: %s - %s - %s",
            meeting.name, meeting.start_time, meeting.end_time
        )
        return meeting

    def get_today_meetings(self) -> list[Meeting]:
        return self._repository.find_by_date(date.today())

    def get_meetings_by_date(self, meeting_date: date) -> list[Meeting]:
        return self._repository.find_by_date(meeting_date)

    def get_total_hours(self, meeting_date: date) -> str:
        meetings = self._repository.find_by_date(meeting_date)
        total_minutes = sum(m.duration_minutes for m in meetings)
        hours = total_minutes // 60
        mins = total_minutes % 60
        if hours > 0 and mins > 0:
            return f"{hours}h{mins}min"
        if hours > 0:
            return f"{hours}h"
        return f"{mins}min"

    def get_meetings_with_index(self, meeting_date: date) -> list[dict]:
        return self._repository.find_by_date_with_index(meeting_date)

    def update_meeting(
        self, meeting_date: date, index: int, name: str, start_time: time, end_time: time,
        card: str | None = None,
    ) -> Meeting:
        try:
            meeting = Meeting(
                name=name.strip(),
                start_time=start_time,
                end_time=end_time,
                date=meeting_date,
                card=card,
            )
        except ValueError as e:
            if "End time" in str(e):
                raise InvalidMeetingDurationError(str(e))
            raise
        if not self._repository.update_by_index(meeting_date, index, meeting):
            raise MeetingNotFoundError("Meeting not found")
        logger.info("Meeting updated at index %s: %s", index, meeting.name)
        return meeting

    def delete_meeting(self, meeting_date: date, index: int) -> bool:
        result = self._repository.delete_by_index(meeting_date, index)
        if result:
            logger.info("Meeting deleted at index %s", index)
        return result

    def update_meeting_by_id(
        self, meeting_date: date, meeting_id: str, name: str,
        start_time: time, end_time: time, card: str | None = None,
    ) -> Meeting:
        try:
            meeting = Meeting(
                name=name.strip(),
                start_time=start_time,
                end_time=end_time,
                date=meeting_date,
                card=card,
            )
        except ValueError as e:
            if "End time" in str(e):
                raise InvalidMeetingDurationError(str(e))
            raise
        meeting.meeting_id = meeting_id
        if not self._repository.update_by_id(meeting_date, meeting_id, meeting):
            raise MeetingNotFoundError("Meeting not found")
        logger.info("Meeting updated by ID %s: %s", meeting_id, meeting.name)
        return meeting

    def delete_meeting_by_id(self, meeting_date: date, meeting_id: str) -> bool:
        result = self._repository.delete_by_id(meeting_date, meeting_id)
        if result:
            logger.info("Meeting deleted by ID %s", meeting_id)
        return result

    def get_total_decimal(self, meeting_date: date) -> str:
        meetings = self._repository.find_by_date(meeting_date)
        total = sum(m.duration_decimal for m in meetings)
        return str(total)

    def get_balance(self, meeting_date: date) -> dict:
        meetings = self._repository.find_by_date(meeting_date)
        total_minutes = sum(m.duration_minutes for m in meetings)
        balance_minutes = settings.daily_target_minutes - total_minutes
        return {"balance_minutes": balance_minutes, "is_overtime": balance_minutes < 0}

    def list_csv_files(self) -> list[dict]:
        return self._repository.list_files()

    def read_csv_file(self, filename: str) -> dict | None:
        return self._repository.read_file(filename)
