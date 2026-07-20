import re
from datetime import date, time
from pathlib import Path

from app.domain.models import Meeting
from app.domain.repositories import MeetingRepository


class CsvMeetingRepository(MeetingRepository):
    _FILENAME_PATTERN = re.compile(r'^Horas_\d{2}-\d{2}-\d{4}\.csv$')
    _HEADER_WITH_ID = "ID;Nome;Início;Fim;Duração;Horas;Card\n"
    _HEADER_LEGACY = "Nome;Início;Fim;Duração;Horas;Card\n"

    def __init__(self, data_dir: str = "data"):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(exist_ok=True)

    def _file_path(self, meeting_date: date) -> Path:
        filename = f"Horas_{meeting_date.strftime('%d-%m-%Y')}.csv"
        return self._data_dir / filename

    def _format_meeting_line(self, meeting: Meeting) -> str:
        card = meeting.card or ""
        return (
            f"{meeting.meeting_id};"
            f"{meeting.name};"
            f"{meeting.start_time.strftime('%H:%M')};"
            f"{meeting.end_time.strftime('%H:%M')};"
            f"{meeting.duration_hours};"
            f"{meeting.duration_decimal};"
            f"{card}\n"
        )

    def _format_meeting_line_legacy(self, meeting: Meeting) -> str:
        card = meeting.card or ""
        return (
            f"{meeting.name};"
            f"{meeting.start_time.strftime('%H:%M')};"
            f"{meeting.end_time.strftime('%H:%M')};"
            f"{meeting.duration_hours};"
            f"{meeting.duration_decimal};"
            f"{card}\n"
        )

    def _has_id_column(self, file_path: Path) -> bool:
        if not file_path.exists():
            return False
        with open(file_path, "r", encoding="utf-8") as f:
            header = f.readline().strip()
        return header.startswith("ID;")

    def save(self, meeting: Meeting) -> None:
        meeting_date = meeting.date or date.today()
        file_path = self._file_path(meeting_date)
        header_needed = not file_path.exists()

        with open(file_path, "a", encoding="utf-8") as f:
            if header_needed:
                f.write(self._HEADER_WITH_ID)
            f.write(self._format_meeting_line(meeting))

    def find_by_date(self, meeting_date: date) -> list[Meeting]:
        file_path = self._file_path(meeting_date)
        if not file_path.exists():
            return []
        return self._parse_file(file_path, meeting_date)

    def find_by_date_with_index(self, meeting_date: date) -> list[dict]:
        file_path = self._file_path(meeting_date)
        if not file_path.exists():
            return []
        meetings = self._parse_file(file_path, meeting_date)
        return [{"meeting": m, "index": i} for i, m in enumerate(meetings)]

    def _parse_file(self, file_path: Path, meeting_date: date) -> list[Meeting]:
        meetings: list[Meeting] = []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return meetings

        has_id = lines[0].strip().startswith("ID;")

        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(";")

            if has_id and len(parts) >= 6:
                meeting_id = parts[0]
                name = parts[1]
                start = time.fromisoformat(parts[2])
                end = time.fromisoformat(parts[3])
                card = parts[6].strip() if len(parts) > 6 else None
            elif len(parts) >= 5:
                meeting_id = None
                name = parts[0]
                start = time.fromisoformat(parts[1])
                end = time.fromisoformat(parts[2])
                card = parts[5].strip() if len(parts) > 5 else None
            else:
                continue

            meeting = Meeting(
                name=name,
                start_time=start,
                end_time=end,
                date=meeting_date,
                card=card or None,
            )
            if meeting_id:
                meeting.meeting_id = meeting_id
            meetings.append(meeting)
        return meetings

    def find_by_id(self, meeting_date: date, meeting_id: str) -> Meeting | None:
        meetings = self.find_by_date(meeting_date)
        for m in meetings:
            if m.meeting_id == meeting_id:
                return m
        return None

    def update_by_index(self, meeting_date: date, index: int, meeting: Meeting) -> bool:
        file_path = self._file_path(meeting_date)
        if not file_path.exists():
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        data_idx = index + 1
        if data_idx >= len(lines):
            return False

        has_id = lines[0].strip().startswith("ID;")
        if has_id:
            lines[data_idx] = self._format_meeting_line(meeting)
        else:
            lines[data_idx] = self._format_meeting_line_legacy(meeting)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True

    def update_by_id(self, meeting_date: date, meeting_id: str, meeting: Meeting) -> bool:
        file_path = self._file_path(meeting_date)
        if not file_path.exists():
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        has_id = lines[0].strip().startswith("ID;")
        if not has_id:
            return False

        for i, line in enumerate(lines[1:], start=1):
            parts = line.strip().split(";")
            if parts and parts[0] == meeting_id:
                lines[i] = self._format_meeting_line(meeting)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                return True
        return False

    def delete_by_index(self, meeting_date: date, index: int) -> bool:
        file_path = self._file_path(meeting_date)
        if not file_path.exists():
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        data_idx = index + 1
        if data_idx >= len(lines):
            return False

        lines.pop(data_idx)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True

    def delete_by_id(self, meeting_date: date, meeting_id: str) -> bool:
        file_path = self._file_path(meeting_date)
        if not file_path.exists():
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        has_id = lines[0].strip().startswith("ID;")
        if not has_id:
            return False

        for i, line in enumerate(lines[1:], start=1):
            parts = line.strip().split(";")
            if parts and parts[0] == meeting_id:
                lines.pop(i)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                return True
        return False

    def exists(self, meeting_date: date) -> bool:
        return self._file_path(meeting_date).exists()

    def list_files(self) -> list[dict]:
        files = sorted(self._data_dir.glob("Horas_*.csv"), reverse=True)
        result = []
        for f in files:
            result.append({
                "filename": f.name,
                "date": f.name.replace("Horas_", "").replace(".csv", ""),
                "size": f.stat().st_size,
            })
        return result

    def read_file(self, filename: str) -> dict | None:
        if not self._FILENAME_PATTERN.match(filename):
            return None
        file_path = (self._data_dir / filename).resolve()
        if not str(file_path).startswith(str(self._data_dir.resolve())):
            return None
        if not file_path.exists() or not file_path.is_file():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return {"header": [], "rows": []}
        header = lines[0].strip().split(";")
        rows = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(";")
            rows.append(dict(zip(header, parts)))
        return {"header": header, "rows": rows, "filename": filename}
