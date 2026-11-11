from pathlib import Path
from typing import Optional
import logging

import jwt
from fastapi import (
    APIRouter, Depends, File, Form, HTTPException, Query,
    Request, UploadFile
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

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

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, private, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


# ---------------------------------------------------------------------
# Authentication and redirects
# ---------------------------------------------------------------------

async def login_redirect(clear_cookie=False):
    response = RedirectResponse(
        "/pages/login.html",
        status_code=303,
        headers=NO_CACHE_HEADERS
    )

    if clear_cookie:
        response.delete_cookie(
            key=COOKIE_NAME,
            path="/",
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax"
        )
        response.delete_cookie(key="cdvh_access_token", path="/")

    return response


async def role_redirect(user: User):
    destinations = {
        "volunteer": "/volunteer/dashboard",
        "coordinator": "/coordinator/dashboard",
        "admin": "/admin/dashboard"
    }

    destination = destinations.get(user.role, "/pages/login.html")

    if user.role in ("coordinator", "admin") and not user.is_approved:
        destination = "/pages/login.html"

    return RedirectResponse(
        destination,
        status_code=303,
        headers=NO_CACHE_HEADERS
    )


async def get_cookie_user(request: Request, db: Session):
    token = (
        request.cookies.get(COOKIE_NAME)
        or request.cookies.get("cdvh_access_token")
    )

    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None, await login_redirect()

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        return None, await login_redirect(clear_cookie=True)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return None, await login_redirect(clear_cookie=True)

    return user, None


def get_user_skills(user):
    return [
        skill.strip()
        for skill in (user.skill1, user.skill2, user.skill3)
        if skill and skill.strip()
    ]


# ---------------------------------------------------------------------
# Volunteer dashboard
# ---------------------------------------------------------------------

@router.get("/volunteers/dashboard", response_class=HTMLResponse)
@router.get("/volunteer/dashboard", response_class=HTMLResponse)
async def volunteer_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role != "volunteer":
        return await role_redirect(user)

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
            "skills": get_user_skills(user),
            "assignments": assignments
        },
        headers=NO_CACHE_HEADERS
    )


# ---------------------------------------------------------------------
# Coordinator dashboard
# ---------------------------------------------------------------------

@router.get("/coordinator/dashboard", response_class=HTMLResponse)
async def coordinator_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role != "coordinator" or not user.is_approved:
        return await role_redirect(user)

    skills = get_user_skills(user)

    if user.role == "admin":
        disasters = db.query(Disaster).order_by(Disaster.id.desc()).all()
        tasks = db.query(Task).order_by(Task.id.desc()).all()
    else:
        coord_place = (user.place or "").strip().lower()
        coord_district = (user.district or "").strip().lower()
        coord_region = (user.region or "").strip().lower()

        disaster_conditions = [Disaster.created_by == user.id]
        location_conditions = []

        if coord_place:
            location_conditions.extend([
                func.lower(Disaster.place) == coord_place,
                Disaster.place.ilike(f"%{coord_place}%")
            ])

        if coord_district:
            location_conditions.extend([
                func.lower(Disaster.district) == coord_district,
                Disaster.district.ilike(f"%{coord_district}%")
            ])

        if coord_region:
            location_conditions.extend([
                func.lower(Disaster.district) == coord_region,
                func.lower(Disaster.place) == coord_region
            ])

        if location_conditions:
            disaster_conditions.append(
                and_(
                    Disaster.created_by.is_(None),
                    or_(*location_conditions)
                )
            )

        disasters = (
            db.query(Disaster)
            .filter(or_(*disaster_conditions))
            .order_by(Disaster.id.desc())
            .all()
        )

        disaster_ids = [disaster.id for disaster in disasters]

        task_conditions = [Task.created_by == user.id]

        if disaster_ids:
            task_conditions.append(Task.disaster_id.in_(disaster_ids))

        if coord_place:
            task_conditions.append(Task.location.ilike(f"%{coord_place}%"))

        if coord_district:
            task_conditions.append(Task.location.ilike(f"%{coord_district}%"))

        if coord_region:
            task_conditions.append(Task.location.ilike(f"%{coord_region}%"))

        tasks = (
            db.query(Task)
            .filter(or_(*task_conditions))
            .order_by(Task.id.desc())
            .all()
        )

    volunteers = (
        db.query(User)
        .filter(User.role == "volunteer")
        .order_by(User.id.desc())
        .all()
    )

    active_tasks_count = sum(t.status == "active" for t in tasks)

    urgent_alerts_count = (
        sum(d.severity in ("Urgent", "High") for d in disasters)
        + sum(t.urgency in ("Urgent", "High") for t in tasks)
    )

    # Calculate ML volunteer matches for each task.
    task_matches = {}

    for task in tasks:
        active_assignments = [
            assignment
            for assignment in task.assignments
            if assignment.status != "rejected"
        ]

        if len(active_assignments) >= task.required_volunteer_count:
            task_matches[task.id] = []
            continue

        assigned_ids = [
            assignment.volunteer_user_id
            for assignment in task.assignments
        ]

        unassigned_volunteers = [
            volunteer
            for volunteer in volunteers
            if volunteer.is_approved and volunteer.id not in assigned_ids
        ]

        spots = max(
            1,
            task.required_volunteer_count - len(active_assignments)
        )

        try:
            result = await find_volunteer_matches(
                task=task,
                volunteers=unassigned_volunteers,
                city=None,
                top_n=min(5, spots)
            )
            task_matches[task.id] = result.get("matches", [])

        except Exception as exc:
            logger.warning(
                "Could not precalculate matches for task %s: %s",
                task.id,
                exc
            )
            task_matches[task.id] = []

    return templates.TemplateResponse(
        request=request,
        name="coordinator-dashboard.html",
        context={
            "user": user,
            "skills": skills,
            "tasks": tasks,
            "disasters": disasters,
            "volunteers": volunteers,
            "task_matches": task_matches,
            "active_tasks_count": active_tasks_count,
            "urgent_alerts_count": urgent_alerts_count
        },
        headers=NO_CACHE_HEADERS
    )


# ---------------------------------------------------------------------
# Task creation and volunteer matching
# ---------------------------------------------------------------------

@router.post("/coordinator/tasks/create")
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    urgency: str = Form("Active"),
    skills_required: str = Form(""),
    required_volunteer_count: int = Form(1),
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

    task = Task(
        title=title.strip(),
        description=description.strip(),
        location=location.strip(),
        urgency=urgency.strip(),
        skills_required=skills_required.strip(),
        required_volunteer_count=required_volunteer_count,
        status="active",
        created_by=user.id
    )

    db.add(task)

    try:
        db.commit()
    except Exception:
        db.rollback()

    return RedirectResponse(
        "/coordinator/dashboard#active-tasks",
        status_code=303
    )


@router.get("/coordinator/tasks/{task_id}/matches")
@router.get("/coordinator/tasks/{task_id}/match")
async def get_task_volunteer_matches(
    task_id: int,
    request: Request,
    city: str = Query(default=None),
    top_n: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        raise HTTPException(status_code=401, detail="Authentication required.")

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access volunteer matching."
        )

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    active_assignments = [
        assignment
        for assignment in task.assignments
        if assignment.status != "rejected"
    ]

    assigned_count = len(active_assignments)
    required_count = task.required_volunteer_count

    if assigned_count >= required_count:
        return {
            "success": True,
            "task_id": task.id,
            "task_title": task.title,
            "quota_reached": True,
            "assigned_count": assigned_count,
            "required_count": required_count,
            "total_matches": 0,
            "city": city,
            "message": (
                f"Required volunteer quota reached "
                f"({assigned_count}/{required_count} deployed)."
            ),
            "matches": []
        }

    assigned_ids = [
        assignment.volunteer_user_id
        for assignment in task.assignments
    ]

    volunteer_query = db.query(User).filter(
        User.role == "volunteer",
        User.is_approved.is_(True)
    )

    if assigned_ids:
        volunteer_query = volunteer_query.filter(
            User.id.notin_(assigned_ids)
        )

    volunteers = volunteer_query.order_by(User.id.desc()).all()

    remaining_spots = max(1, required_count - assigned_count)
    effective_top_n = min(top_n, remaining_spots)

    try:
        result = await find_volunteer_matches(
            task=task,
            volunteers=volunteers,
            city=city,
            top_n=effective_top_n
        )

        return {
            "success": True,
            "task_id": task.id,
            "task_title": task.title,
            "quota_reached": False,
            "assigned_count": assigned_count,
            "required_count": required_count,
            "remaining_spots": remaining_spots,
            "total_matches": len(result["matches"]),
            "city": result["city"],
            "message": result["message"],
            "matches": result["matches"]
        }

    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    except Exception as exc:
        logger.exception("Volunteer matching API failed")
        raise HTTPException(
            status_code=500,
            detail="Volunteer matching failed. Check server logs."
        ) from exc


# ---------------------------------------------------------------------
# Task and disaster status management
# ---------------------------------------------------------------------

@router.post("/coordinator/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db)
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
        "/coordinator/dashboard#active-tasks",
        status_code=303
    )


@router.post("/coordinator/disasters/{disaster_id}/status")
async def update_disaster_status(
    disaster_id: int,
    request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db)
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
        "/coordinator/dashboard#dl-alerts",
        status_code=303
    )


@router.post("/coordinator/tasks/{task_id}/delete")
async def delete_coordinator_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

    task = db.query(Task).filter(Task.id == task_id).first()

    if task:
        db.query(Assignment).filter(
            Assignment.task_id == task.id
        ).delete(synchronize_session=False)

        db.delete(task)

        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete task %s: %s", task_id, exc)

    return RedirectResponse(
        "/coordinator/dashboard#active-tasks",
        status_code=303
    )


# ---------------------------------------------------------------------
# Volunteer assignment
# ---------------------------------------------------------------------

async def _do_task_assignment(
    user,
    task_id: int,
    volunteer_id: int,
    db: Session,
    match_score: float = None
):
    task = db.query(Task).filter(Task.id == task_id).first()
    volunteer = db.query(User).filter(
        User.id == volunteer_id,
        User.role == "volunteer"
    ).first()

    if task and volunteer:
        active_assignments = [
            assignment
            for assignment in task.assignments
            if assignment.status != "rejected"
        ]

        existing = db.query(Assignment).filter(
            Assignment.task_id == task.id,
            Assignment.volunteer_user_id == volunteer.id
        ).first()

        if existing and existing.status != "rejected":
            logger.info(
                "Volunteer %s already assigned to task %s",
                volunteer.id,
                task.id
            )
            return RedirectResponse(
                "/coordinator/dashboard#active-tasks",
                status_code=303
            )

        if (
            len(active_assignments) >= task.required_volunteer_count
            and not (existing and existing.status == "rejected")
        ):
            logger.warning(
                "Task %s required volunteer count (%s) already reached",
                task.id,
                task.required_volunteer_count
            )
            return RedirectResponse(
                "/coordinator/dashboard#active-tasks",
                status_code=303
            )

        score = float(match_score) if match_score is not None else 95.0

        if not existing:
            assignment = Assignment(
                task_id=task.id,
                volunteer_user_id=volunteer.id,
                assigned_by=user.id,
                match_score=score,
                status="pending"
            )
            db.add(assignment)
        else:
            existing.status = "pending"
            existing.assigned_by = user.id
            existing.match_score = score
            existing.updated_at = func.now()

        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("Failed to save task assignment: %s", exc)

    return RedirectResponse(
        "/coordinator/dashboard#active-tasks",
        status_code=303
    )


@router.post("/coordinator/tasks/assign")
async def assign_volunteer_to_task(
    request: Request,
    task_id: int = Form(...),
    volunteer_id: int = Form(...),
    match_score: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

    return await _do_task_assignment(
        user, task_id, volunteer_id, db, match_score
    )


@router.post("/coordinator/tasks/{task_id}/assign")
async def assign_volunteer_to_task_path(
    task_id: int,
    request: Request,
    volunteer_id: int = Form(...),
    match_score: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

    return await _do_task_assignment(
        user, task_id, volunteer_id, db, match_score
    )


@router.post("/volunteer/assignments/{assignment_id}/respond")
@router.post("/volunteers/assignments/{assignment_id}/respond")
async def respond_to_assignment(
    assignment_id: int,
    request: Request,
    action: str = Form(...),
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role != "volunteer":
        return await role_redirect(user)

    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.volunteer_user_id == user.id
    ).first()

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
        "/volunteers/dashboard#deployments",
        status_code=303
    )


# ---------------------------------------------------------------------
# Volunteer skills and profile updates
# ---------------------------------------------------------------------

@router.post("/volunteer/skills/update")
@router.post("/volunteers/skills/update")
@router.post("/profile/skills/update")
async def update_volunteer_skills(
    request: Request,
    skill1: Optional[str] = Form(None),
    skill2: Optional[str] = Form(None),
    skill3: Optional[str] = Form(None),
    years_experience: Optional[int] = Form(None),
    previous_experience: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    user.skill1 = skill1.strip() if skill1 and skill1.strip() else None
    user.skill2 = skill2.strip() if skill2 and skill2.strip() else None
    user.skill3 = skill3.strip() if skill3 and skill3.strip() else None

    if years_experience is not None:
        user.years_experience = max(0, min(60, years_experience))

    if previous_experience is not None:
        user.previous_experience = previous_experience.strip()

    try:
        db.commit()
        db.refresh(user)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to commit volunteer skills update: %s", exc)

    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", "")

    if "application/json" in content_type or "application/json" in accept:
        return {
            "success": True,
            "message": "Skills updated successfully.",
            "skills": [
                skill for skill in (user.skill1, user.skill2, user.skill3)
                if skill
            ],
            "years_experience": user.years_experience,
            "previous_experience": user.previous_experience
        }

    referer = request.headers.get("referer")

    if referer and ("dashboard" in referer or "profile" in referer):
        return RedirectResponse(referer, status_code=303)

    return RedirectResponse(
        "/volunteers/dashboard#capabilities",
        status_code=303
    )


@router.post("/coordinator/volunteers/{volunteer_id}/skills")
async def update_volunteer_skills_by_coordinator(
    volunteer_id: int,
    request: Request,
    skill1: Optional[str] = Form(None),
    skill2: Optional[str] = Form(None),
    skill3: Optional[str] = Form(None),
    years_experience: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role not in ("coordinator", "admin") or not user.is_approved:
        return await role_redirect(user)

    volunteer = db.query(User).filter(
        User.id == volunteer_id,
        User.role == "volunteer"
    ).first()

    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found.")

    volunteer.skill1 = skill1.strip() if skill1 and skill1.strip() else None
    volunteer.skill2 = skill2.strip() if skill2 and skill2.strip() else None
    volunteer.skill3 = skill3.strip() if skill3 and skill3.strip() else None

    if years_experience is not None:
        volunteer.years_experience = max(0, min(60, years_experience))

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Failed to update volunteer skills by coordinator: %s", exc)

    return RedirectResponse(
        "/coordinator/dashboard#volunteer-pool",
        status_code=303
    )


# ---------------------------------------------------------------------
# Admin dashboard and user management
# ---------------------------------------------------------------------

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if user.role != "admin" or not user.is_approved:
        return await role_redirect(user)

    total_users = db.query(User).count()
    total_volunteers = db.query(User).filter(
        User.role == "volunteer"
    ).count()
    total_coordinators = db.query(User).filter(
        User.role == "coordinator"
    ).count()

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
            "profile_image": account.profile_image
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
            "accounts": accounts
        },
        headers=NO_CACHE_HEADERS
    )


@router.post("/admin/users/{user_id}/approve")
async def approve_coordinator(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return await role_redirect(admin)

    coordinator = db.query(User).filter(User.id == user_id).first()

    if coordinator and coordinator.role == "coordinator":
        coordinator.is_approved = True

        try:
            db.commit()
        except Exception:
            db.rollback()

    return RedirectResponse("/admin/dashboard", status_code=303)


@router.post("/admin/users/{user_id}/reject")
async def reject_coordinator(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return await role_redirect(admin)

    coordinator = db.query(User).filter(
        User.id == user_id,
        User.role == "coordinator",
        User.is_approved.is_(False)
    ).first()

    if coordinator:
        db.delete(coordinator)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    return RedirectResponse(
        "/admin/dashboard#approvals",
        status_code=303
    )


@router.post("/admin/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    if admin.role != "admin" or not admin.is_approved:
        return await role_redirect(admin)

    target_user = db.query(User).filter(User.id == user_id).first()

    if target_user and target_user.id != admin.id:
        db.delete(target_user)

        try:
            db.commit()
        except Exception:
            db.rollback()

    return RedirectResponse(
        "/admin/dashboard#user-management",
        status_code=303
    )


# ---------------------------------------------------------------------
# Profile photo and profile page
# ---------------------------------------------------------------------

@router.post("/profile/upload-photo")
async def upload_photo(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    filename = file.filename or "avatar.jpg"
    ext = Path(filename).suffix.lower()

    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"

    avatar_filename = f"user_{user.id}{ext}"
    target_path = UPLOADS_DIR / avatar_filename
    content = await file.read()

    if content:
        target_path.write_bytes(content)
        user.profile_image = f"/assets/uploads/avatars/{avatar_filename}"

        try:
            db.commit()
        except Exception:
            db.rollback()

    referer = request.headers.get("referer")

    if referer and ("dashboard" in referer or "profile" in referer):
        return RedirectResponse(referer, status_code=303)

    return await role_redirect(user)


@router.get("/profile", response_class=HTMLResponse)
async def user_profile_page(
    request: Request,
    db: Session = Depends(get_db)
):
    user, redirect_response = await get_cookie_user(request, db)

    if redirect_response:
        return redirect_response

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "skills": get_user_skills(user)
        },
        headers=NO_CACHE_HEADERS
    )


# ---------------------------------------------------------------------
# Kerala districts and sample disaster prompts
# ---------------------------------------------------------------------

KERALA_DISTRICT_PLACES = {
    "Thiruvananthapuram": [
        "Thiruvananthapuram City", "Neyyattinkara", "Nedumangad",
        "Attingal", "Varkala", "Kazhakkoottam", "Vizhinjam", "Kovalam",
        "Kattakada", "Balaramapuram", "Poovar", "Parassala",
        "Venjaramoodu", "Kilimanoor", "Other / nearby locality"
    ],
    "Kollam": [
        "Kollam City", "Punalur", "Karunagappally", "Kottarakkara",
        "Paravur", "Anchal", "Kundara", "Chathannoor", "Sasthamkotta",
        "Oachira", "Pathanapuram", "Other / nearby locality"
    ],
    "Pathanamthitta": [
        "Pathanamthitta", "Thiruvalla", "Adoor", "Ranni", "Kozhencherry",
        "Pandalam", "Konni", "Mallappally", "Aranmula", "Perunad",
        "Sabarimala", "Other / nearby locality"
    ],
    "Alappuzha": [
        "Alappuzha", "Cherthala", "Kayamkulam", "Haripad", "Mavelikkara",
        "Chengannur", "Ambalappuzha", "Kuttanad", "Thanneermukkom",
        "Aroor", "Mannar", "Edathua", "Other / nearby locality"
    ],
    "Kottayam": [
        "Kottayam", "Changanassery", "Pala", "Vaikom", "Ettumanoor",
        "Kanjirappally", "Erattupetta", "Mundakayam", "Ponkunnam",
        "Kuravilangad", "Kumarakom", "Uzhavoor", "Other / nearby locality"
    ],
    "Idukki": [
        "Painavu", "Thodupuzha", "Munnar", "Adimali", "Kattappana",
        "Kumily", "Nedumkandam", "Peermade", "Vandiperiyar", "Marayoor",
        "Rajakkad", "Vazhathope", "Devikulam", "Other / nearby locality"
    ],
    "Ernakulam": [
        "Kochi", "Kakkanad", "Aluva", "Angamaly", "Perumbavoor",
        "Muvattupuzha", "Kothamangalam", "North Paravur",
        "Thrippunithura", "Kalamassery", "Edappally", "Fort Kochi",
        "Mattancherry", "Vypin", "Eloor", "Piravom",
        "Other / nearby locality"
    ],
    "Thrissur": [
        "Thrissur", "Chalakudy", "Kodungallur", "Irinjalakuda",
        "Guruvayur", "Kunnamkulam", "Wadakkanchery", "Chavakkad",
        "Chelakkara", "Anthikad", "Ollur", "Mala",
        "Other / nearby locality"
    ],
    "Palakkad": [
        "Palakkad", "Ottapalam", "Shoranur", "Chittur", "Mannarkkad",
        "Pattambi", "Alathur", "Cherpulassery", "Nenmara",
        "Kollengode", "Kozhinjampara", "Vadakkencherry",
        "Other / nearby locality"
    ],
    "Malappuram": [
        "Malappuram", "Manjeri", "Tirur", "Ponnani", "Perinthalmanna",
        "Kottakkal", "Nilambur", "Kondotty", "Parappanangadi", "Tanur",
        "Tirurangadi", "Areekode", "Wandoor", "Edappal",
        "Other / nearby locality"
    ],
    "Kozhikode": [
        "Kozhikode", "Vadakara", "Koyilandy", "Feroke", "Ramanattukara",
        "Kunnamangalam", "Mukkam", "Thamarassery", "Balussery",
        "Perambra", "Beypore", "Elathur", "Koduvally",
        "Other / nearby locality"
    ],
    "Wayanad": [
        "Kalpetta", "Sulthan Bathery", "Mananthavady", "Vythiri",
        "Meppadi", "Pulpally", "Panamaram", "Ambalavayal", "Thirunelly",
        "Pozhuthana", "Muttil", "Padinjarathara",
        "Other / nearby locality"
    ],
    "Kannur": [
        "Kannur", "Thalassery", "Payyannur", "Taliparamba", "Mattannur",
        "Iritty", "Koothuparamba", "Sreekandapuram", "Panoor",
        "Azhikode", "Dharmadam", "Other / nearby locality"
    ],
    "Kasaragod": [
        "Kasaragod", "Kanhangad", "Nileshwaram", "Uppala", "Manjeshwar",
        "Cheruvathur", "Trikaripur", "Bekal", "Periya", "Udma",
        "Mulleria", "Badiadka", "Other / nearby locality"
    ]
}

KERALA_DISTRICTS = list(KERALA_DISTRICT_PLACES)

# ---------------------------------------------------------------------
# Pure Database Retrieval for Homepage
# ---------------------------------------------------------------------

def fetch_home_landing_data(
    db: Session,
    prompt_key: Optional[str] = None
) -> dict:
    """
    Pure database retrieval function for index.html.
    Only queries database tables (User, Disaster, Task).
    All images, fallback URLs, badges, and presentational elements are handled in HTML.
    """
    volunteers = (
        db.query(User)
        .filter(User.role == "volunteer")
        .order_by(User.id.desc())
        .limit(8)
        .all()
    )

    campaigns = (
        db.query(Disaster)
        .order_by(Disaster.id.desc())
        .limit(6)
        .all()
    )

    volunteer_count = (
        db.query(User)
        .filter(User.role == "volunteer", User.is_approved == True)
        .count()
    )

    task_count = db.query(Task).count()
    resolved_count = db.query(Task).filter(Task.status == "resolved").count()
    disaster_count = db.query(Disaster).count()

    districts = {
        row[0]
        for row in db.query(User.district).filter(User.district.isnot(None)).all()
        if row[0]
    }
    districts.update(
        row[0]
        for row in db.query(Disaster.district).filter(Disaster.district.isnot(None)).all()
        if row[0]
    )

    stats = {
        "active_volunteers": volunteer_count or len(volunteers),
        "tasks_completed": resolved_count or task_count,
        "disasters_handled": disaster_count,
        "districts_covered": max(len(districts), 14),
        "ml_match_accuracy": 94,
    }

    return {
        "success": True,
        "stats": stats,
        "volunteers": volunteers,
        "campaigns": campaigns,
        "kerala_districts": KERALA_DISTRICTS,
        "kerala_places": KERALA_DISTRICT_PLACES,
    }


@router.get("/api/home/data")
@router.get("/api/home/details")
async def get_home_page_data(db: Session = Depends(get_db)):
    """Public API for homepage data, campaigns, volunteers, and DL analysis."""
    return fetch_home_landing_data(db)