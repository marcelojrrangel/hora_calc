from datetime import date, time

import pytest

from app.domain.models import Meeting
from app.infrastructure.csv_repository import CsvMeetingRepository


@pytest.fixture
def repo(temp_data_dir):
    return CsvMeetingRepository(data_dir=str(temp_data_dir))


class TestSaveAndFind:
    def test_save_and_find_by_date(self, repo, sample_meeting):
        repo.save(sample_meeting)
        meetings = repo.find_by_date(date(2026, 7, 19))
        assert len(meetings) == 1
        assert meetings[0].name == "Daily Scrum"
        assert meetings[0].start_time == time(9, 0)
        assert meetings[0].end_time == time(9, 15)

    def test_save_with_card(self, repo, another_meeting):
        repo.save(another_meeting)
        meetings = repo.find_by_date(date(2026, 7, 19))
        assert meetings[0].card == "CARD-123"

    def test_find_by_date_no_file(self, repo):
        meetings = repo.find_by_date(date(2026, 7, 19))
        assert meetings == []

    def test_find_by_date_wrong_date(self, repo, sample_meeting):
        repo.save(sample_meeting)
        meetings = repo.find_by_date(date(2026, 7, 20))
        assert meetings == []

    def test_multiple_meetings_same_day(self, repo, sample_meeting, another_meeting):
        repo.save(sample_meeting)
        repo.save(another_meeting)
        meetings = repo.find_by_date(date(2026, 7, 19))
        assert len(meetings) == 2


class TestExists:
    def test_exists_true(self, repo, sample_meeting):
        repo.save(sample_meeting)
        assert repo.exists(date(2026, 7, 19))

    def test_exists_false(self, repo):
        assert not repo.exists(date(2026, 7, 19))


class TestUpdateByIndex:
    def test_update_success(self, repo, sample_meeting):
        repo.save(sample_meeting)
        updated = type(sample_meeting)(
            name="Updated", start_time=time(10, 0), end_time=time(11, 0),
            date=date(2026, 7, 19),
        )
        assert repo.update_by_index(date(2026, 7, 19), 0, updated)
        meetings = repo.find_by_date(date(2026, 7, 19))
        assert meetings[0].name == "Updated"
        assert meetings[0].start_time == time(10, 0)

    def test_update_out_of_range(self, repo, sample_meeting):
        repo.save(sample_meeting)
        updated = type(sample_meeting)(
            name="X", start_time=time(10, 0), end_time=time(11, 0),
            date=date(2026, 7, 19),
        )
        assert not repo.update_by_index(date(2026, 7, 19), 5, updated)

    def test_update_no_file(self, repo):
        updated = type("M", (), {})()
        assert not repo.update_by_index(date(2026, 7, 19), 0, updated)


class TestDeleteByIndex:
    def test_delete_success(self, repo, sample_meeting):
        repo.save(sample_meeting)
        assert repo.delete_by_index(date(2026, 7, 19), 0)
        assert repo.find_by_date(date(2026, 7, 19)) == []

    def test_delete_out_of_range(self, repo, sample_meeting):
        repo.save(sample_meeting)
        assert not repo.delete_by_index(date(2026, 7, 19), 5)

    def test_delete_no_file(self, repo):
        assert not repo.delete_by_index(date(2026, 7, 19), 0)


class TestFindByDateWithIndex:
    def test_with_index(self, repo, sample_meeting, another_meeting):
        repo.save(sample_meeting)
        repo.save(another_meeting)
        items = repo.find_by_date_with_index(date(2026, 7, 19))
        assert len(items) == 2
        assert items[0]["index"] == 0
        assert items[0]["meeting"].name == "Daily Scrum"
        assert items[1]["index"] == 1
        assert items[1]["meeting"].name == "Sprint Planning"

    def test_no_file(self, repo):
        assert repo.find_by_date_with_index(date(2026, 7, 19)) == []


class TestListFiles:
    def test_list_empty(self, repo):
        assert repo.list_files() == []

    def test_list_with_files(self, repo, sample_meeting):
        repo.save(sample_meeting)
        files = repo.list_files()
        assert len(files) >= 1
        assert "Horas_19-07-2026.csv" in files[0]["filename"]


class TestReadFile:
    def test_read_valid_file(self, repo, sample_meeting):
        repo.save(sample_meeting)
        data = repo.read_file("Horas_19-07-2026.csv")
        assert data is not None
        assert len(data["rows"]) == 1
        assert data["rows"][0]["Nome"] == "Daily Scrum"

    def test_read_nonexistent_file(self, repo):
        assert repo.read_file("nonexistent.csv") is None


class TestPathTraversal:
    def test_reject_path_traversal(self, repo):
        result = repo.read_file("../../etc/passwd")
        assert result is None

    def test_reject_invalid_pattern(self, repo):
        result = repo.read_file("not_a_valid_file.csv")
        assert result is None

    def test_accept_valid_pattern(self, repo, sample_meeting):
        repo.save(sample_meeting)
        result = repo.read_file("Horas_19-07-2026.csv")
        assert result is not None


class TestMeetingId:
    def test_save_with_id(self, repo, sample_meeting):
        repo.save(sample_meeting)
        meetings = repo.find_by_date(date(2026, 7, 19))
        assert len(meetings) == 1
        assert meetings[0].meeting_id == sample_meeting.meeting_id

    def test_find_by_id(self, repo, sample_meeting):
        repo.save(sample_meeting)
        found = repo.find_by_id(date(2026, 7, 19), sample_meeting.meeting_id)
        assert found is not None
        assert found.name == sample_meeting.name

    def test_find_by_id_not_found(self, repo, sample_meeting):
        repo.save(sample_meeting)
        found = repo.find_by_id(date(2026, 7, 19), "nonexistent")
        assert found is None

    def test_update_by_id(self, repo, sample_meeting):
        repo.save(sample_meeting)
        updated = Meeting(
            name="Updated",
            start_time=time(10, 0),
            end_time=time(11, 0),
            date=date(2026, 7, 19),
        )
        updated.meeting_id = sample_meeting.meeting_id
        assert repo.update_by_id(date(2026, 7, 19), sample_meeting.meeting_id, updated)
        meetings = repo.find_by_date(date(2026, 7, 19))
        assert meetings[0].name == "Updated"

    def test_update_by_id_not_found(self, repo, sample_meeting):
        repo.save(sample_meeting)
        updated = Meeting(
            name="X",
            start_time=time(10, 0),
            end_time=time(11, 0),
            date=date(2026, 7, 19),
        )
        assert not repo.update_by_id(date(2026, 7, 19), "nonexistent", updated)

    def test_delete_by_id(self, repo, sample_meeting):
        repo.save(sample_meeting)
        assert repo.delete_by_id(date(2026, 7, 19), sample_meeting.meeting_id)
        assert repo.find_by_date(date(2026, 7, 19)) == []

    def test_delete_by_id_not_found(self, repo, sample_meeting):
        repo.save(sample_meeting)
        assert not repo.delete_by_id(date(2026, 7, 19), "nonexistent")
