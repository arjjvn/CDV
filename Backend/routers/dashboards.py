from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

import jwt
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from Backend.database_dependency import get_db
from Backend.models import User, Task, Assignment, Disaster
from Backend.auth.config import SECRET_KEY, ALGORITHM
from Backend.ml_model import find_volunteer_matches

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Dashboards"])

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

PAGES_DIR = FRONTEND_DIR / "pages"
UPLOADS_DIR = FRONTEND_DIR / "assets" / "uploads" / "avatars"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(PAGES_DIR))

COOKIE_NAME = "access_token"
COOKIE_SECURE = False




async def login_redirect(clear_cookie=False):
    response = RedirectResponse(
        url="/pages/login.html",
        status_code=303
    )

    if clear_cookie:
        response.delete_cookie(
            key=COOKIE_NAME,
            path="/",
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax",
        )

    return response


async def role_redirect(user: User):
    if user.role == "volunteer":
        destination = "/volunteer/dashboard"
    elif user.role == "coordinator" and user.is_approved:
        destination = "/coordinator/dashboard"
    elif user.role == "admin" and user.is_approved:
        destination = "/admin/dashboard"
    else:
        destination = "/pages/login.html"

    return RedirectResponse(url=destination, status_code=303)


async def get_cookie_user(request: Request, db: Session):

    token = request.cookies.get(COOKIE_NAME) or request.cookies.get("cdvh_access_token")

    if not token:
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None, await login_redirect()

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = int(payload["sub"])

    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        return None, await login_redirect(clear_cookie=True)

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        return None, await login_redirect(clear_cookie=True)

    return user, None


@router.get("/volunteers/dashboard", response_class=HTMLResponse)
@router.get("/volunteer/dashboard", response_class=HTMLResponse)
async def volunteer_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):

    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role != "volunteer":
        return await role_redirect(user)

    skills = [
        skill.strip()
        for skill in (user.skill1, user.skill2, user.skill3)
        if skill and skill.strip()
    ]

    # Retrieve all assigned deployment tasks for this volunteer
    assignments = (
        db.query(Assignment)
        .filter(Assignment.volunteer_user_id == user.id)
        .order_by(Assignment.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="volunteer-dashboard.html",
        context={
            "user": user,
            "skills": skills,
            "assignments": assignments,
        },
    )





@router.get("/coordinator/dashboard", response_class=HTMLResponse)
async def coordinator_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):

    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role != "coordinator" or not user.is_approved:
        return await role_redirect(user)

    skills = [
        skill.strip()
        for skill in (user.skill1, user.skill2, user.skill3)
        if skill and skill.strip()
    ]

    # Fetch live tasks from database created by coordinators or emergency dispatches
    tasks = db.query(Task).order_by(Task.id.desc()).all()

    # Fetch live disaster alerts triaged via Deep Learning
    disasters = db.query(Disaster).order_by(Disaster.id.desc()).all()

    volunteers = (
        db.query(User)
        .filter(User.role == "volunteer")
        .order_by(User.id.desc())
        .all()
    )

    active_tasks_count = (
        db.query(Task)
        .filter(Task.status == "active")
        .count()
    )

    urgent_alerts_count = (
        db.query(Disaster)
        .filter(Disaster.severity.in_(["Urgent", "High"]))
        .count()
        + db.query(Task)
        .filter(Task.urgency.in_(["Urgent", "High"]))
        .count()
    )

    return templates.TemplateResponse(
        request=request,
        name="coordinator-dashboard.html",
        context={
            "user": user,
            "skills": skills,
            "tasks": tasks,
            "disasters": disasters,
            "volunteers": volunteers,
            "active_tasks_count": active_tasks_count,
            "urgent_alerts_count": urgent_alerts_count,
        },
    )





@router.post("/coordinator/tasks/create")
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    urgency: str = Form("Active"),
    skills_required: str = Form(""),
    required_volunteer_count: int = Form(1),
    db: Session = Depends(get_db),
):

    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

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

    return RedirectResponse(
        url="/coordinator/dashboard#active-tasks",
        status_code=303
    )



# ----------------------------------------------------------------------
# API: FIND MATCHING VOLUNTEERS
# ----------------------------------------------------------------------

@router.get("/coordinator/tasks/{task_id}/matches")
@router.get("/coordinator/tasks/{task_id}/match")
async def get_task_volunteer_matches(
    task_id: int,
    request: Request,
    city: str = Query(default=None),
    top_n: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db)
):

    # Authentication
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    # Authorization
    if user.role not in ("coordinator", "admin") or not user.is_approved:

        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access volunteer matching."
        )

    # Find task
    task = (
        db.query(Task)
        .filter(Task.id == task_id)
        .first()
    )

    if not task:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    # Fetch approved volunteers
    volunteers = (
        db.query(User)
        .filter(
            User.role == "volunteer",
            User.is_approved.is_(True)
        )
        .order_by(User.id.desc())
        .all()
    )

    # Execute asynchronous ML matching
    try:

        result = await find_volunteer_matches(
            task=task,
            volunteers=volunteers,
            city=city,
            top_n=top_n
        )

        return {
            "success": True,
            "task_id": task.id,
            "task_title": task.title,
            "total_matches": len(result["matches"]),
            "city": result["city"],
            "message": result["message"],
            "matches": result["matches"]
        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc)
        )

    except Exception as exc:

        logger.exception("Volunteer matching API failed")

        raise HTTPException(
            status_code=500,
            detail="Volunteer matching failed. Check server logs."
        ) from exc



@router.post("/coordinator/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db),
):

    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

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

    return RedirectResponse(
        url="/coordinator/dashboard#active-tasks",
        status_code=303
    )


@router.post("/coordinator/disasters/{disaster_id}/status")
async def update_disaster_status(
    disaster_id: int,
    request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db),
):
    user, redirect_response = await get_cookie_user(request, db)
    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if disaster:
        disaster.status = new_status.strip().capitalize()
        try:
            db.commit()
        except Exception:
            db.rollback()

    return RedirectResponse(
        url="/coordinator/dashboard#dl-alerts",
        status_code=303
    )


async def _do_task_assignment(user, task_id: int, volunteer_id: int, db: Session, match_score: float = None):
    task = db.query(Task).filter(Task.id == task_id).first()
    volunteer = db.query(User).filter(User.id == volunteer_id, User.role == "volunteer").first()

    if task and volunteer:
        existing = db.query(Assignment).filter(
            Assignment.task_id == task.id,
            Assignment.volunteer_user_id == volunteer.id,
        ).first()

        score = float(match_score) if match_score is not None else 95.0

        if not existing:
            assignment = Assignment(
                task_id=task.id,
                volunteer_user_id=volunteer.id,
                assigned_by=user.id,
                match_score=score,
                status="pending",
            )
            db.add(assignment)
            try:
                db.commit()
            except Exception:
                db.rollback()
        else:
            # Re-activate if was previously rejected or updated
            existing.status = "pending"
            existing.assigned_by = user.id
            existing.match_score = score
            existing.updated_at = func.now()
            try:
                db.commit()
            except Exception:
                db.rollback()

    return RedirectResponse(
        url="/coordinator/dashboard#active-tasks",
        status_code=303
    )


@router.post("/coordinator/tasks/assign")
async def assign_volunteer_to_task(
    request: Request,
    task_id: int = Form(...),
    volunteer_id: int = Form(...),
    match_score: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

    return await _do_task_assignment(user, task_id, volunteer_id, db, match_score=match_score)


@router.post("/coordinator/tasks/{task_id}/assign")
async def assign_volunteer_to_task_path(
    task_id: int,
    request: Request,
    volunteer_id: int = Form(...),
    match_score: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

    return await _do_task_assignment(user, task_id, volunteer_id, db, match_score=match_score)


# ----------------------------------------------------------------------
# VOLUNTEER ASSIGNMENT RESPONSE (ACCEPT / REJECT)
# ----------------------------------------------------------------------

@router.post("/volunteer/assignments/{assignment_id}/respond")
@router.post("/volunteers/assignments/{assignment_id}/respond")
async def respond_to_assignment(
    assignment_id: int,
    request: Request,
    action: str = Form(...),  # "accept" or "reject"
    db: Session = Depends(get_db),
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role != "volunteer":
        return await role_redirect(user)

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.volunteer_user_id == user.id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Deployment assignment not found or not addressed to your account."
        )

    clean_action = action.strip().lower()

    if clean_action in ("accept", "accepted"):
        assignment.status = "accepted"
    elif clean_action in ("reject", "rejected", "decline", "declined"):
        assignment.status = "rejected"

    assignment.updated_at = func.now()

    try:
        db.commit()
    except Exception:
        db.rollback()

    return RedirectResponse(
        url="/volunteers/dashboard#deployments",
        status_code=303
    )


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):

    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role != "admin" or not user.is_approved:
        return await role_redirect(user)

    total_users = db.query(User).count()

    total_volunteers = (
        db.query(User)
        .filter(User.role == "volunteer")
        .count()
    )

    total_coordinators = (
        db.query(User)
        .filter(User.role == "coordinator")
        .count()
    )

    pending_coordinators = (
        db.query(User)
        .filter(
            User.role == "coordinator",
            User.is_approved.is_(False)
        )
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
async def approve_coordinator(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):

    admin, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return await role_redirect(admin)

    coordinator = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if coordinator and coordinator.role == "coordinator":
        coordinator.is_approved = True

        try:
            db.commit()
        except Exception:
            db.rollback()

    return RedirectResponse(
        url="/admin/dashboard",
        status_code=303
    )







@router.post("/admin/users/{user_id}/reject")
async def reject_coordinator(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):

    admin, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return await role_redirect(admin)

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
        status_code=303
    )







@router.post("/admin/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):

    admin, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return await role_redirect(admin)

    target_user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if target_user and target_user.id != admin.id:
        db.delete(target_user)

        try:
            db.commit()
        except Exception:
            db.rollback()

    return RedirectResponse(
        url="/admin/dashboard#user-management",
        status_code=303
    )







@router.post("/profile/upload-photo")
async def upload_photo(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    filename = file.filename or "avatar.jpg"

    ext = Path(filename).suffix.lower()

    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext = ".jpg"

    avatar_filename = f"user_{user.id}{ext}"
    target_path = UPLOADS_DIR / avatar_filename

    content = await file.read()

    if content:
        with open(target_path, "wb") as f:
            f.write(content)

        user.profile_image = (
            f"/assets/uploads/avatars/{avatar_filename}"
        )

        try:
            db.commit()
        except Exception:
            db.rollback()

    referer = request.headers.get("referer")

    if referer and ("dashboard" in referer or "profile" in referer):
        return RedirectResponse(
            url=referer,
            status_code=303
        )

    return await role_redirect(user)







@router.get("/profile", response_class=HTMLResponse)
async def user_profile_page(
    request: Request,
    db: Session = Depends(get_db),
):

    user, redirect_response = await get_cookie_user(request, db)

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
    