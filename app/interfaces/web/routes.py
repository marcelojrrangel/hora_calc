from datetime import date, time
from pathlib import Path

from fastapi import APIRouter, Cookie, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

from app.auth import (
    clear_session_cookie,
    create_session,
    destroy_session,
    set_session_cookie,
    validate_session,
    verify_password,
)
from app.config import settings, today
from app.rate_limiter import login_rate_limiter
from app.domain.exceptions import InvalidFilenameError, MeetingNotFoundError
from app.use_cases.meeting_use_cases import MeetingUseCases

router = APIRouter()

_template_dir = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_template_dir)), autoescape=True)


def _get_use_cases(request: Request) -> MeetingUseCases:
    return request.app.state.use_cases


def _check_auth(session_token: str | None) -> bool:
    return session_token is not None and validate_session(session_token)


def _format_minutes(minutes: int) -> str:
    minutes = max(minutes, 0)
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours}h{mins}min"
    if hours > 0:
        return f"{hours}h"
    return f"{mins}min"


@router.get("/login", response_class=HTMLResponse)
async def login_page(session_token: str | None = Cookie(None)):
    if _check_auth(session_token):
        return RedirectResponse("/", status_code=302)
    template = _env.get_template("login.html")
    return HTMLResponse(template.render())


@router.post("/login")
async def login(request: Request, password: str = Form(...)):
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    client_ip = client_ip.split(",")[0].strip() if client_ip else "unknown"
    if login_rate_limiter.is_limited(client_ip):
        retry_after = login_rate_limiter.retry_after(client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts",
            headers={"Retry-After": str(retry_after)},
        )
    if not verify_password(password):
        login_rate_limiter.record_attempt(client_ip)
        raise HTTPException(status_code=401, detail="Senha incorreta")
    login_rate_limiter.reset(client_ip)
    token = create_session()
    response = RedirectResponse(url="/", status_code=302)
    set_session_cookie(response, token)
    return response


@router.get("/logout")
async def logout(session_token: str | None = Cookie(None)):
    if session_token:
        destroy_session(session_token)
    response = RedirectResponse(url="/login", status_code=302)
    clear_session_cookie(response)
    return response


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, session_token: str | None = Cookie(None)):
    if not _check_auth(session_token):
        return RedirectResponse(url="/login", status_code=302)
    uc = _get_use_cases(request)
    today_date = today()
    meetings = uc.get_meetings_by_date(today_date)
    total = uc.get_total_hours(today_date)
    balance = uc.get_balance(today_date)
    balance_text = _format_minutes(abs(balance["balance_minutes"]))
    template = _env.get_template("index.html")
    html = template.render(
        meetings=meetings,
        total=total,
        balance=balance,
        balance_text=balance_text,
        today=today_date.strftime("%d/%m/%Y"),
    )
    return HTMLResponse(html)


@router.post("/registrar")
async def register(
    request: Request,
    session_token: str | None = Cookie(None),
    nome: str = Form(...),
    inicio: str = Form(...),
    fim: str = Form(...),
    card: str = Form(""),
):
    if not _check_auth(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    uc = _get_use_cases(request)
    try:
        start_time = time.fromisoformat(inicio)
        end_time = time.fromisoformat(fim)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format")
    meeting = uc.register_meeting(
        nome, start_time, end_time, card=card.strip() or None
    )
    return {"success": True, "meeting": meeting.name}


@router.get("/reunioes")
async def get_meetings(
    request: Request,
    session_token: str | None = Cookie(None),
    data: str | None = Query(None),
):
    if not _check_auth(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    uc = _get_use_cases(request)
    meeting_date = date.fromisoformat(data) if data else today()
    items = uc.get_meetings_with_index(meeting_date)
    total = uc.get_total_hours(meeting_date)
    balance = uc.get_balance(meeting_date)
    return [
        {
            "index": item["index"],
            "name": item["meeting"].name,
            "start": item["meeting"].start_time.strftime("%H:%M"),
            "end": item["meeting"].end_time.strftime("%H:%M"),
            "duration": item["meeting"].duration_hours,
            "card": item["meeting"].card,
        }
        for item in items
    ] + [{"total": total, "balance_minutes": balance["balance_minutes"]}]


@router.put("/reunioes/{index}")
async def update_meeting(
    request: Request,
    index: int,
    session_token: str | None = Cookie(None),
    nome: str = Form(...),
    inicio: str = Form(...),
    fim: str = Form(...),
    card: str = Form(""),
    data: str | None = Form(None),
):
    if not _check_auth(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    uc = _get_use_cases(request)
    try:
        start_time = time.fromisoformat(inicio)
        end_time = time.fromisoformat(fim)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format")
    meeting_date = date.fromisoformat(data) if data else today()
    meeting = uc.update_meeting(
        meeting_date, index, nome, start_time, end_time, card=card.strip() or None
    )
    return {"success": True, "meeting": meeting.name}


@router.delete("/reunioes/{index}")
async def delete_meeting(
    request: Request,
    index: int,
    session_token: str | None = Cookie(None),
    data: str | None = Query(None),
):
    if not _check_auth(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    uc = _get_use_cases(request)
    meeting_date = date.fromisoformat(data) if data else today()
    if not uc.delete_meeting(meeting_date, index):
        raise MeetingNotFoundError("Meeting not found")
    return {"success": True}


@router.get("/calculadora", response_class=HTMLResponse)
async def calculator(request: Request, session_token: str | None = Cookie(None)):
    if not _check_auth(session_token):
        return RedirectResponse(url="/login", status_code=302)
    template = _env.get_template("calculadora.html")
    html = template.render()
    return HTMLResponse(html)


@router.get("/resumo")
async def summary(
    request: Request,
    session_token: str | None = Cookie(None),
    data: str | None = Query(None),
):
    if not _check_auth(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    uc = _get_use_cases(request)
    meeting_date = date.fromisoformat(data) if data else today()
    meetings = uc.get_meetings_by_date(meeting_date)
    total = uc.get_total_hours(meeting_date)
    total_dec = uc.get_total_decimal(meeting_date)
    return {
        "total": total,
        "total_decimal": total_dec,
        "count": len(meetings),
        "date": meeting_date.strftime("%d/%m/%Y"),
    }


@router.get("/resumo/restante")
async def remaining(request: Request, session_token: str | None = Cookie(None)):
    if not _check_auth(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    uc = _get_use_cases(request)
    today_date = today()
    meetings = uc.get_meetings_by_date(today_date)
    total_minutes = sum(m.duration_minutes for m in meetings)
    remaining_minutes = max(0, settings.daily_target_minutes - total_minutes)
    hours = remaining_minutes // 60
    mins = remaining_minutes % 60
    return {
        "used_minutes": total_minutes,
        "remaining_minutes": remaining_minutes,
        "remaining_hours": f"{hours}h{mins}min" if hours > 0 else f"{mins}min",
        "remaining_decimal": round(remaining_minutes / 60, 2),
    }


@router.get("/csv-viewer", response_class=HTMLResponse)
async def csv_viewer(request: Request, session_token: str | None = Cookie(None)):
    if not _check_auth(session_token):
        return RedirectResponse(url="/login", status_code=302)
    template = _env.get_template("csv-viewer.html")
    html = template.render()
    return HTMLResponse(html)


@router.get("/csv-files")
async def list_csv_files(request: Request, session_token: str | None = Cookie(None)):
    if not _check_auth(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    uc = _get_use_cases(request)
    return uc.list_csv_files()


@router.get("/csv-files/{filename:path}")
async def get_csv_file(
    request: Request,
    filename: str,
    session_token: str | None = Cookie(None),
):
    if not _check_auth(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    uc = _get_use_cases(request)
    data = uc.read_csv_file(filename)
    if data is None:
        raise InvalidFilenameError(f"File not found: {filename}")
    return data
