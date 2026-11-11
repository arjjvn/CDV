from pathlib import Path
from typing import Optional
import json
import logging
from urllib.parse import quote, unquote

from fastapi import FastAPI, Request, Depends, Query, Form
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from starlette.concurrency import run_in_threadpool

from Backend.auth import routes as auth_routes
from Backend.auth import protected
from Backend.auth.routes import verify_password, hash_password, create_access_token
from Backend.database import create_tables
from Backend.database_dependency import get_db
from Backend import models
from Backend.routers import chatbot
from Backend.routers import dashboards
from Backend.routers import health
from Backend.routers import emergency
from Backend.routers.dashboards import (
    fetch_home_landing_data,
    KERALA_DISTRICTS,
    KERALA_DISTRICT_PLACES,
    NO_CACHE_HEADERS,
)
from Backend.routers.emergency import report_emergency_endpoint
from RAG.retrieval import rag

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Community Disaster Volunteer Hub (CDVH)",
    description="API for AI-assisted disaster volunteer matching, deep learning triage, and coordination.",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
PAGES_DIR = FRONTEND_DIR / "pages"


templates = Jinja2Templates(directory=str(FRONTEND_DIR))


@app.on_event("startup")
def startup():
    create_tables()


# ----------------------------------------------------------------------
# ROOT & TEMPLATE PAGE REDIRECTS (PREVENT RAW STATIC JINJA ACCESS)
# ----------------------------------------------------------------------

@app.get("/")
def home(
    request: Request,
    prompt: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        data = fetch_home_landing_data(db, prompt_key=prompt)
        raw_history = request.cookies.get("cdvh_chat_history")
        try:
            chat_history = json.loads(unquote(raw_history)) if raw_history else []
        except Exception:
            chat_history = []

        chat_open = (request.query_params.get("chat") == "open")

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "stats": data.get("stats", {}),
                "volunteers": data.get("volunteers", []),
                "campaigns": data.get("campaigns", []),
                "dl_sample": data.get("dl_sample", {}),
                "active_prompt": prompt or "default",
                "kerala_districts": data.get("kerala_districts", []),
                "kerala_places": data.get("kerala_places", {}),
                "report_status": status,
                "chat_history": chat_history,
                "chat_open": chat_open,
            }
        )
    except Exception as e:
        logger.warning("Could not render dynamic index.html via Jinja: %s", e)
        return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/chat")
async def handle_home_chat(
    request: Request,
    question: str = Form(...)
):
    raw_history = request.cookies.get("cdvh_chat_history")
    try:
        chat_history = json.loads(unquote(raw_history)) if raw_history else []
    except Exception:
        chat_history = []

    clean_q = question.strip()
    if clean_q:
        try:
            bot_answer = await run_in_threadpool(rag, clean_q)
        except Exception as exc:
            logger.error("RAG error: %s", exc)
            bot_answer = "I am currently unable to retrieve specific disaster guidelines. Please contact the 112 Emergency Hotline for immediate relief."

        chat_history.append({"sender": "user", "text": clean_q})
        chat_history.append({"sender": "bot", "text": bot_answer})
        chat_history = chat_history[-10:]

    res = RedirectResponse(url="/?chat=open#chatWindow", status_code=303)
    res.set_cookie(key="cdvh_chat_history", value=quote(json.dumps(chat_history)), max_age=86400, path="/")
    return res


@app.post("/chat/clear")
def handle_clear_chat():
    res = RedirectResponse(url="/?chat=open#chatWindow", status_code=303)
    res.delete_cookie(key="cdvh_chat_history", path="/")
    return res


@app.post("/report")
async def handle_home_emergency_report(
    request: Request,
    db: Session = Depends(get_db)
):
    """Processes public emergency distress alerts from index.html form using Python DL pipeline."""
    try:
        await report_emergency_endpoint(request, db)
    except Exception as exc:
        logger.error("Failed to process public emergency report: %s", exc)
    return RedirectResponse(url="/?status=reported#heroEmergencyForm", status_code=303)


# ----------------------------------------------------------------------
# BACKEND AUTHENTICATION (PURE PYTHON & JINJA — NO CLIENT JS NEEDED)
# ----------------------------------------------------------------------

@app.get("/login")
@app.get("/pages/login.html")
def render_login_page(
    request: Request,
    mode: Optional[str] = Query("login"),
    tab: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    msg: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    current_mode = (tab or mode or "login").lower()
    return templates.TemplateResponse(
        request=request,
        name="pages/login.html",
        context={
            "request": request,
            "mode": current_mode,
            "error": error,
            "msg": msg,
            "kerala_districts": KERALA_DISTRICTS,
            "kerala_places": KERALA_DISTRICT_PLACES,
        },
        headers=NO_CACHE_HEADERS
    )


@app.post("/login")
@app.post("/pages/login.html")
async def handle_login(
    request: Request,
    username_or_email: str = Form(...),
    password: str = Form(...),
    role: str = Form("volunteer"),
    db: Session = Depends(get_db)
):
    identifier = username_or_email.strip().lower()
    user = (
        db.query(models.User)
        .filter(or_(func.lower(models.User.email) == identifier, func.lower(models.User.username) == identifier))
        .first()
    )

    if not user or not verify_password(password, user.hashed_password):
        err = quote("Invalid username/email or password. Please try again.")
        return RedirectResponse(url=f"/pages/login.html?mode=login&error={err}", status_code=303, headers=NO_CACHE_HEADERS)

    if user.role != role:
        err = quote(f"Role mismatch. This account is registered as '{user.role}'. Please select '{user.role.title()}'.")
        return RedirectResponse(url=f"/pages/login.html?mode=login&error={err}", status_code=303, headers=NO_CACHE_HEADERS)

    if user.role in ("coordinator", "admin") and not user.is_approved:
        err = quote("Account pending approval. Please contact an administrator.")
        return RedirectResponse(url=f"/pages/login.html?mode=login&error={err}", status_code=303, headers=NO_CACHE_HEADERS)

    # Success: Create session token & set cookies
    token = create_access_token(user)
    dashboards = {
        "volunteer": "/volunteers/dashboard",
        "coordinator": "/coordinator/dashboard",
        "admin": "/admin/dashboard"
    }
    destination = dashboards.get(user.role, "/volunteers/dashboard")

    res = RedirectResponse(url=destination, status_code=303, headers=NO_CACHE_HEADERS)
    res.set_cookie(key="access_token", value=token, httponly=True, samesite="lax", path="/")
    res.set_cookie(key="cdvh_access_token", value=token, path="/")
    res.set_cookie(key="cdvh_user_role", value=user.role, path="/")
    return res


@app.post("/register")
async def handle_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: Optional[str] = Form(None),
    role: str = Form("volunteer"),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    place: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    pincode: Optional[str] = Form(None),
    blood_group: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    skill1: Optional[str] = Form(None),
    skill2: Optional[str] = Form(None),
    skill3: Optional[str] = Form(None),
    years_experience: Optional[int] = Form(None),
    previous_experience: Optional[str] = Form(None),
    available_from: Optional[str] = Form(None),
    available_to: Optional[str] = Form(None),
    languages: Optional[str] = Form(None),
    organization: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    from datetime import datetime

    norm_email = email.strip().lower()
    norm_user = (username.strip().lower() if username and username.strip() else norm_email.split("@")[0].strip())

    existing = (
        db.query(models.User)
        .filter(or_(func.lower(models.User.email) == norm_email, func.lower(models.User.username) == norm_user))
        .first()
    )
    if existing:
        err = quote("An account with this username or email already exists.")
        return RedirectResponse(url=f"/pages/login.html?mode=register&error={err}", status_code=303, headers=NO_CACHE_HEADERS)

    # Parse shift times and dob
    af_time = None
    at_time = None
    dob_date = None

    if date_of_birth and date_of_birth.strip():
        try:
            dob_date = datetime.strptime(date_of_birth.strip(), "%Y-%m-%d").date()
        except Exception:
            pass

    if available_from:
        try:
            af_time = datetime.strptime(available_from.strip(), "%H:%M").time()
        except Exception:
            pass
    if available_to:
        try:
            at_time = datetime.strptime(available_to.strip(), "%H:%M").time()
        except Exception:
            pass

    is_appr = (role == "volunteer")

    new_user = models.User(
        username=norm_user,
        email=norm_email,
        hashed_password=hash_password(password),
        role=role,
        is_approved=is_appr,
        first_name=first_name.strip() if first_name else None,
        last_name=last_name.strip() if last_name else None,
        phone=phone.strip() if phone else None,
        district=district.strip() if district else None,
        place=place.strip() if place else None,
        address=address.strip() if address else None,
        pincode=pincode.strip() if pincode else None,
        date_of_birth=dob_date,
        blood_group=blood_group.strip() if blood_group else None,
        gender=gender.strip() if gender else None,
        skill1=skill1.strip() if skill1 else None,
        skill2=skill2.strip() if skill2 else None,
        skill3=skill3.strip() if skill3 else None,
        years_experience=years_experience if years_experience is not None else 0,
        previous_experience=previous_experience.strip() if previous_experience else None,
        available_from=af_time,
        available_to=at_time,
        languages=languages.strip() if languages else None,
        organization=organization.strip() if organization else None,
        region=region.strip() if region else None,
    )

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception as exc:
        db.rollback()
        err = quote(f"Registration failed: {str(exc)}")
        return RedirectResponse(url=f"/pages/login.html?mode=register&error={err}", status_code=303, headers=NO_CACHE_HEADERS)

    if role == "volunteer":
        token = create_access_token(new_user)
        res = RedirectResponse(url="/volunteers/dashboard", status_code=303, headers=NO_CACHE_HEADERS)
        res.set_cookie(key="access_token", value=token, httponly=True, samesite="lax", path="/")
        res.set_cookie(key="cdvh_access_token", value=token, path="/")
        res.set_cookie(key="cdvh_user_role", value="volunteer", path="/")
        return res
    else:
        msg = quote("Registration submitted successfully! Coordinator accounts require administrator approval before logging in.")
        return RedirectResponse(url=f"/pages/login.html?mode=login&msg={msg}", status_code=303, headers=NO_CACHE_HEADERS)


@app.post("/coordinator/field-report")
async def handle_coordinator_field_report(
    request: Request,
    location: str = Form(""),
    situation: str = Form("Field Ops"),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    combined_desc = f"[Field Report - {situation}] {notes} (Sector: {location})"
    try:
        from Backend.dl_model import understand_message_sync
        analysis = understand_message_sync(combined_desc)
        new_disaster = models.Disaster(
            title=f"Field Report: {situation} at {location or 'Kerala'}",
            description=combined_desc,
            disaster_type=analysis.get("disaster", "Emergency").capitalize(),
            severity=analysis.get("urgency", "Medium").capitalize(),
            status="Active",
            place=location or "Kerala",
            district="Kerala",
        )
        db.add(new_disaster)
        db.commit()
    except Exception as e:
        logger.error("Failed to log coordinator field report: %s", e)
        db.rollback()

    return RedirectResponse(url="/coordinator/dashboard#incident-reporting", status_code=303, headers=NO_CACHE_HEADERS)


@app.get("/logout")
@app.post("/logout")
def root_logout():
    res = RedirectResponse(url="/pages/login.html", status_code=303, headers=NO_CACHE_HEADERS)
    res.delete_cookie(key="access_token", path="/", httponly=True, samesite="lax")
    res.delete_cookie(key="cdvh_access_token", path="/")
    res.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'
    return res


@app.get("/pages/volunteer-dashboard.html")
def redirect_volunteer_page():
    return RedirectResponse(url="/volunteers/dashboard", status_code=303, headers=NO_CACHE_HEADERS)


@app.get("/pages/coordinator-dashboard.html")
def redirect_coordinator_page():
    return RedirectResponse(url="/coordinator/dashboard", status_code=303, headers=NO_CACHE_HEADERS)


@app.get("/pages/admin-dashboard.html")
def redirect_admin_page():
    return RedirectResponse(url="/admin/dashboard", status_code=303, headers=NO_CACHE_HEADERS)


@app.get("/pages/profile.html")
def redirect_profile_page():
    return RedirectResponse(url="/profile", status_code=303, headers=NO_CACHE_HEADERS)


# ----------------------------------------------------------------------
# STATIC FILE MOUNTS
# ----------------------------------------------------------------------

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/pages", StaticFiles(directory=PAGES_DIR), name="pages")


# ----------------------------------------------------------------------
# ROUTER INCLUSIONS
# ----------------------------------------------------------------------

app.include_router(health.router)
app.include_router(emergency.router)
app.include_router(auth_routes.router)
app.include_router(protected.router)
app.include_router(chatbot.router)
app.include_router(dashboards.router)
