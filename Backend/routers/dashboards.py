import os
from pathlib import Path
from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from Backend.database_dependency import get_db
from Backend.models import User, Task, Disaster, Assignment
from Backend.auth.config import SECRET_KEY, ALGORITHM


router = APIRouter(tags=["Dashboards"])

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"
if not FRONTEND_DIR.is_dir():
    FRONTEND_DIR = BASE_DIR / "Frontend"

PAGES_DIR = FRONTEND_DIR / "pages"
UPLOADS_DIR = FRONTEND_DIR / "assets" / "uploads" / "avatars"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(PAGES_DIR))

COOKIE_NAME = "access_token"
COOKIE_SECURE = False  # Set True when deployed using HTTPS


def login_redirect(clear_cookie=False):
    response = RedirectResponse(url="/pages/login.html", status_code=303)
    if clear_cookie:
        response.delete_cookie(
            key=COOKIE_NAME,
            path="/",
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax",
        )
    return response


def role_redirect(user: User):
    if user.role == "volunteer":
        destination = "/volunteers/dashboard"
    elif user.role == "coordinator" and user.is_approved:
        destination = "/coordinator/dashboard"
    elif user.role == "admin" and user.is_approved:
        destination = "/admin/dashboard"
    else:
        destination = "/pages/login.html"

    return RedirectResponse(url=destination, status_code=303)


def get_cookie_user(request: Request, db: Session):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        # Check Authorization header as fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None, login_redirect()

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        return None, login_redirect(clear_cookie=True)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return None, login_redirect(clear_cookie=True)

    return user, None


def ensure_seed_tasks(db: Session, admin_or_coord_id: int = None):
    """Seed initial sample response tasks if none exist yet."""
    if db.query(Task).count() == 0:
        seed_tasks = [
            Task(
                title="Medical Triage & First Aid",
                description="Establish emergency triage at Sector 4 Relief Camp. Coordinate with ambulance teams.",
                location="Sector 4 Relief Camp, Highway Road",
                urgency="Urgent",
                status="active",
                required_volunteer_count=3,
                skills_required="First Aid, CPR, Triage",
                created_by=admin_or_coord_id,
            ),
            Task(
                title="Food & Drinking Water Distribution",
                description="Organize packaging and supply distribution line for affected families.",
                location="Town Hall, Chengannur",
                urgency="Active",
                status="active",
                required_volunteer_count=4,
                skills_required="Logistics, General Relief",
                created_by=admin_or_coord_id,
            ),
            Task(
                title="Search & River Bank Rescue",
                description="Deploy trained rescue personnel along River Bank bridge road checkpoint.",
                location="River Bank, Bridge Road",
                urgency="Urgent",
                status="pending",
                required_volunteer_count=5,
                skills_required="Rescue, Swimming, Navigation",
                created_by=admin_or_coord_id,
            ),
        ]
        for t in seed_tasks:
            db.add(t)
        try:
            db.commit()
        except Exception:
            db.rollback()


# --------------------------------------------------
# VOLUNTEER DASHBOARD (supports both plural and singular)
# --------------------------------------------------

@router.get("/volunteers/dashboard", response_class=HTMLResponse)
@router.get("/volunteer/dashboard", response_class=HTMLResponse)
def volunteer_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    user, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    if user.role != "volunteer":
        return role_redirect(user)

    skills = [
        skill.strip()
        for skill in (user.skill1, user.skill2, user.skill3)
        if skill and skill.strip()
    ]

    return templates.TemplateResponse(
        request=request,
        name="volunteer-dashboard.html",
        context={
            "user": user,
            "skills": skills,
        },
    )


# --------------------------------------------------
# COORDINATOR DASHBOARD
# --------------------------------------------------

@router.get("/coordinator/dashboard", response_class=HTMLResponse)
def coordinator_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    user, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    if user.role != "coordinator" or not user.is_approved:
        return role_redirect(user)

    skills = [
        skill.strip()
        for skill in (user.skill1, user.skill2, user.skill3)
        if skill and skill.strip()
    ]

    ensure_seed_tasks(db, admin_or_coord_id=user.id)

    tasks = db.query(Task).order_by(Task.id.desc()).all()
    volunteers = db.query(User).filter(User.role == "volunteer").order_by(User.id.desc()).all()

    active_tasks_count = db.query(Task).filter(Task.status == "active").count()
    urgent_alerts_count = db.query(Task).filter(Task.urgency == "Urgent").count()

    return templates.TemplateResponse(
        request=request,
        name="coordinator-dashboard.html",
        context={
            "user": user,
            "skills": skills,
            "tasks": tasks,
            "volunteers": volunteers,
            "active_tasks_count": active_tasks_count,
            "urgent_alerts_count": urgent_alerts_count,
        },
    )


# --------------------------------------------------
# COORDINATOR TASK ACTIONS
# --------------------------------------------------

@router.post("/coordinator/tasks/create")
def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    urgency: str = Form("Active"),
    skills_required: str = Form(""),
    required_volunteer_count: int = Form(1),
    db: Session = Depends(get_db),
):
    user, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return role_redirect(user)

    new_task = Task(
        title=title.strip(),
        description=description.strip(),
        location=location.strip(),
        urgency=urgency.strip(),
        skills_required=skills_required.strip(),
        required_volunteer_count=required_volunteer_count,
        status="active",
        created_by=user.id,
    )
    db.add(new_task)
    try:
        db.commit()
    except Exception:
        db.rollback()

    return RedirectResponse(url="/coordinator/dashboard#active-tasks", status_code=303)


@router.post("/coordinator/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db),
):
    user, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return role_redirect(user)

    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = new_status.strip().lower()
        if new_status.lower() == "resolved":
            task.urgency = "Resolved"
        elif new_status.lower() == "active":
            task.urgency = "Active"
        try:
            db.commit()
        except Exception:
            db.rollback()

    return RedirectResponse(url="/coordinator/dashboard#active-tasks", status_code=303)


# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------

@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    user, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    if user.role != "admin" or not user.is_approved:
        return role_redirect(user)

    total_users = db.query(User).count()
    total_volunteers = db.query(User).filter(User.role == "volunteer").count()
    total_coordinators = db.query(User).filter(User.role == "coordinator").count()
    pending_coordinators = (
        db.query(User)
        .filter(User.role == "coordinator", User.is_approved.is_(False))
        .order_by(User.id)
        .all()
    )
    all_users = db.query(User).order_by(User.id.desc()).all()

    accounts = [
        {
            "id": account.id,
            "username": account.username,
            "first_name": account.first_name,
            "last_name": account.last_name,
            "email": account.email,
            "role": account.role,
            "is_approved": account.is_approved,
            "district": account.district,
            "skill1": account.skill1,
            "skill2": account.skill2,
            "skill3": account.skill3,
            "profile_image": account.profile_image,
        }
        for account in all_users
    ]

    return templates.TemplateResponse(
        request=request,
        name="admin-dashboard.html",
        context={
            "user": user,
            "total_users": total_users,
            "total_volunteers": total_volunteers,
            "total_coordinators": total_coordinators,
            "pending_coordinators": pending_coordinators,
            "accounts": accounts,
        },
    )


@router.post("/admin/users/{user_id}/approve")
def approve_coordinator(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    admin, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return role_redirect(admin)

    coordinator = db.query(User).filter(User.id == user_id).first()
    if coordinator and coordinator.role == "coordinator":
        coordinator.is_approved = True
        try:
            db.commit()
        except Exception:
            db.rollback()

    return RedirectResponse(url="/admin/dashboard", status_code=303)

@router.post("/admin/users/{user_id}/reject")
def reject_coordinator(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    admin, redirect_response = get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return role_redirect(admin)

    coordinator = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.role == "coordinator",
            User.is_approved.is_(False),
        )
        .first()
    )

    if coordinator:
        db.delete(coordinator)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    return RedirectResponse(
        url="/admin/dashboard#approvals",
        status_code=303,
    )

@router.post("/admin/users/{user_id}/delete")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    admin, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return role_redirect(admin)

    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user and target_user.id != admin.id:
        db.delete(target_user)
        try:
            db.commit()
        except Exception:
            db.rollback()

    return RedirectResponse(url="/admin/dashboard#user-management", status_code=303)


# --------------------------------------------------
# PHOTO UPLOAD (OPTIONAL PHOTO FOR PROFILE)
# --------------------------------------------------

@router.post("/profile/upload-photo")
async def upload_photo(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    filename = file.filename or "avatar.jpg"
    ext = Path(filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext = ".jpg"

    avatar_filename = f"user_{user.id}{ext}"
    target_path = UPLOADS_DIR / avatar_filename

    content = await file.read()
    if len(content) > 0:
        with open(target_path, "wb") as f:
            f.write(content)

        user.profile_image = f"/assets/uploads/avatars/{avatar_filename}"
        try:
            db.commit()
        except Exception:
            db.rollback()

    referer = request.headers.get("referer")
    if referer and ("dashboard" in referer or "profile" in referer):
        return RedirectResponse(url=referer, status_code=303)

    return role_redirect(user)


# --------------------------------------------------
# DEDICATED PROFILE VIEW / EDIT PAGE
# --------------------------------------------------

@router.get("/profile", response_class=HTMLResponse)
def user_profile_page(
    request: Request,
    db: Session = Depends(get_db),
):
    user, redirect_response = get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    skills = [
        skill.strip()
        for skill in (user.skill1, user.skill2, user.skill3)
        if skill and skill.strip()
    ]

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "skills": skills,
        },
    )
