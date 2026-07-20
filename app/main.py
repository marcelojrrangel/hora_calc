import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.domain.exceptions import (
    InvalidFilenameError,
    InvalidMeetingDurationError,
    MeetingError,
    MeetingNotFoundError,
)
from app.infrastructure.csv_repository import CsvMeetingRepository
from app.interfaces.web.routes import router
from app.use_cases.meeting_use_cases import MeetingUseCases

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def create_app() -> FastAPI:
    app = FastAPI(title="Somador de Horas")

    def _error_response(status_code: int, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.__class__.__name__,
                "detail": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(InvalidMeetingDurationError)
    async def invalid_duration_handler(request, exc):
        return _error_response(400, exc)

    @app.exception_handler(MeetingNotFoundError)
    async def not_found_handler(request, exc):
        return _error_response(404, exc)

    @app.exception_handler(InvalidFilenameError)
    async def invalid_filename_handler(request, exc):
        return _error_response(400, exc)

    @app.exception_handler(MeetingError)
    async def meeting_error_handler(request, exc):
        return _error_response(400, exc)

    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return _error_response(400, exc)

    repository = CsvMeetingRepository()
    use_cases = MeetingUseCases(repository)

    app.state.use_cases = use_cases

    app.mount("/static", StaticFiles(directory="app/interfaces/web/static"), name="static")
    app.include_router(router)

    return app


app = create_app()
