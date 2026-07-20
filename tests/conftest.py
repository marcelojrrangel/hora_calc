from datetime import date, time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.domain.models import Meeting


@pytest.fixture
def temp_data_dir():
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_meeting() -> Meeting:
    return Meeting(
        name="Daily Scrum",
        start_time=time(9, 0),
        end_time=time(9, 15),
        date=date(2026, 7, 19),
    )


@pytest.fixture
def another_meeting() -> Meeting:
    return Meeting(
        name="Sprint Planning",
        start_time=time(10, 0),
        end_time=time(12, 0),
        date=date(2026, 7, 19),
        card="CARD-123",
    )
