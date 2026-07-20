from abc import ABC, abstractmethod
from datetime import date

from app.domain.models import Meeting


class MeetingRepository(ABC):
    @abstractmethod
    def save(self, meeting: Meeting) -> None:
        pass

    @abstractmethod
    def find_by_date(self, meeting_date: date) -> list[Meeting]:
        pass

    @abstractmethod
    def find_by_date_with_index(self, meeting_date: date) -> list[dict]:
        pass

    @abstractmethod
    def find_by_id(self, meeting_date: date, meeting_id: str) -> Meeting | None:
        pass

    @abstractmethod
    def update_by_index(self, meeting_date: date, index: int, meeting: Meeting) -> bool:
        pass

    @abstractmethod
    def update_by_id(self, meeting_date: date, meeting_id: str, meeting: Meeting) -> bool:
        pass

    @abstractmethod
    def delete_by_index(self, meeting_date: date, index: int) -> bool:
        pass

    @abstractmethod
    def delete_by_id(self, meeting_date: date, meeting_id: str) -> bool:
        pass

    @abstractmethod
    def exists(self, meeting_date: date) -> bool:
        pass

    @abstractmethod
    def list_files(self) -> list[dict]:
        pass

    @abstractmethod
    def read_file(self, filename: str) -> dict | None:
        pass
