import logging
from typing import Optional, List
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session

from Backend.database_dependency import get_db
from Backend.models import Disaster, Task, User
from Backend.dl_model import analyze_emergency_message
from Backend.ml_model import find_volunteer_matches

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Emergency & Deep Learning"])


# ----------------------------------------------------------------------
# PYDANTIC SCHEMAS
# ----------------------------------------------------------------------

class MessageAnalyzeRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, description="Emergency distress text")


class EmergencyReportRequest(BaseModel):
    message: Optional[str] = None
    description: Optional[str] = None
    district: Optional[str] = None
    place: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


# ----------------------------------------------------------------------
# 1) DEEP LEARNING MESSAGE ANALYSIS ENDPOINT
# ----------------------------------------------------------------------

@router.post("/emergency/analyze")
async def analyze_message_endpoint(
    request: Request,
):
    """
    Direct endpoint for Deep Learning NLP message classification.
    Processes distress messages using the multi-head MLP neural network.
    Returns: skill, urgency, disaster, confidence scores, and emergency flag.
    """
    text = ""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            text = (body.get("message") or body.get("description") or "").strip()
        except Exception:
            pass

    if not text:
        try:
            form = await request.form()
            text = (form.get("message") or form.get("description") or "").strip()
        except Exception:
            pass

    if not text:
        text = (request.query_params.get("message") or request.query_params.get("description") or "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="Emergency message text cannot be empty.")

    try:
        analysis = await analyze_emergency_message(text)
        return {
            "success": True,
            "message": text,
            "analysis": analysis,
            "skill": analysis.get("skill"),
            "skill_conf": analysis.get("skill_conf"),
            "urgency": analysis.get("urgency"),
            "urgency_conf": analysis.get("urgency_conf"),
            "disaster": analysis.get("disaster"),
            "disaster_conf": analysis.get("disaster_conf"),
            "is_emergency": analysis.get("is_emergency"),
        }
    except Exception as exc:
        logger.exception("Error in Deep Learning message analysis: %s", exc)
        raise HTTPException(status_code=500, detail=f"DL analysis failed: {str(exc)}")


# ----------------------------------------------------------------------
# 2) EMERGENCY REPORT & AUTOMATED DISPATCH ENDPOINT
# ----------------------------------------------------------------------

@router.post("/emergency/report")
async def report_emergency_endpoint(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Full emergency reporting endpoint:
    1. Analyzes distress text using the Deep Learning model.
    2. Registers an active Disaster record in the database.
    3. Creates a corresponding emergency response Task.
    4. Triggers the Scikit-learn ML volunteer matching engine to find candidate volunteers.
    """
    # Extract data from either JSON or Form data
    district = None
    place = None
    text = None
    contact_name = None
    contact_phone = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = await request.json()
            text = (data.get("description") or data.get("message") or "").strip()
            district = data.get("district")
            place = data.get("place")
            contact_name = data.get("contact_name")
            contact_phone = data.get("contact_phone")
        except Exception:
            pass

    if not text:
        form = await request.form()
        text = (form.get("description") or form.get("message") or "").strip()
        district = form.get("district")
        place = form.get("place")
        contact_name = form.get("contact_name")
        contact_phone = form.get("contact_phone")

    if not text:
        raise HTTPException(status_code=400, detail="Emergency description is required.")

    # 1. Run Deep Learning classification
    analysis = await analyze_emergency_message(text)

    disaster_label = analysis.get("disaster", "Unknown")
    urgency_label = analysis.get("urgency", "medium")
    skill_label = analysis.get("skill", "Unknown")

    # Map urgency to platform severity
    if urgency_label == "high":
        severity = "Urgent"
        task_urgency = "Urgent"
        required_vols = 3
    elif urgency_label == "low":
        severity = "Low"
        task_urgency = "Active"
        required_vols = 1
    else:
        severity = "Medium"
        task_urgency = "Active"
        required_vols = 2

    clean_disaster_type = disaster_label.capitalize() if disaster_label != "Unknown" else "Emergency"
    clean_skill = skill_label if skill_label != "Unknown" else "General Relief"

    location_str = ", ".join(filter(None, [place, district])) or "Kerala"

    # 2. Create Disaster Record
    disaster_title = f"{clean_disaster_type} Alert at {location_str}"
    new_disaster = Disaster(
        title=disaster_title[:150],
        disaster_type=clean_disaster_type[:100],
        description=text,
        district=district,
        place=place,
        severity=severity,
        status="Active",
    )
    db.add(new_disaster)

    try:
        db.commit()
        db.refresh(new_disaster)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save disaster record: %s", exc)
        raise HTTPException(status_code=500, detail="Database failure creating disaster record.")

    # 3. Create Corresponding Task
    task_title = f"Dispatch: {clean_skill} Support ({clean_disaster_type})"
    new_task = Task(
        disaster_id=new_disaster.id,
        title=task_title[:150],
        description=f"{text}\n(Contact: {contact_name or 'N/A'}, Phone: {contact_phone or 'N/A'})" if (contact_name or contact_phone) else text,
        location=location_str[:150],
        urgency=task_urgency,
        status="active",
        skills_required=clean_skill,
        required_volunteer_count=required_vols,
    )
    db.add(new_task)

    try:
        db.commit()
        db.refresh(new_task)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save task record: %s", exc)
        raise HTTPException(status_code=500, detail="Database failure creating response task.")

    # 4. Trigger Volunteer Matching via ML model
    matched_volunteers = []
    try:
        volunteers = (
            db.query(User)
            .filter(User.role == "volunteer", User.is_approved.is_(True))
            .all()
        )
        match_result = await find_volunteer_matches(
            task=new_task,
            volunteers=volunteers,
            city=place or district,
            top_n=5,
        )
        matched_volunteers = match_result.get("matches", [])
    except Exception as exc:
        logger.warning("Automated volunteer matching non-critical warning: %s", exc)

    return {
        "success": True,
        "message": "Emergency alert registered and analyzed successfully.",
        "disaster_id": new_disaster.id,
        "task_id": new_task.id,
        "location": location_str,
        "task": {
            "id": new_task.id,
            "title": new_task.title,
            "urgency": new_task.urgency,
            "skills_required": new_task.skills_required,
            "required_volunteers": new_task.required_volunteer_count,
        },
        "disaster": {
            "id": new_disaster.id,
            "title": new_disaster.title,
            "severity": new_disaster.severity,
            "disaster_type": new_disaster.disaster_type,
        },
        "analysis": {
            "disaster": disaster_label,
            "disaster_conf": analysis.get("disaster_conf"),
            "urgency": urgency_label,
            "urgency_conf": analysis.get("urgency_conf"),
            "skill": skill_label,
            "skill_conf": analysis.get("skill_conf"),
            "is_emergency": analysis.get("is_emergency"),
        },
        "matched_volunteers": matched_volunteers,
        "matched_count": len(matched_volunteers),
    }


# ----------------------------------------------------------------------
# 3) PUBLIC DATA ENDPOINTS (DISASTERS, TASKS, VOLUNTEERS)
# ----------------------------------------------------------------------

@router.get("/disasters")
def list_disasters(db: Session = Depends(get_db)):
    """Retrieve all active or reported disasters."""
    disasters = db.query(Disaster).order_by(Disaster.id.desc()).all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "disaster_type": d.disaster_type,
            "description": d.description,
            "district": d.district,
            "place": d.place,
            "severity": d.severity,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "tasks_count": len(d.tasks) if d.tasks else 0,
        }
        for d in disasters
    ]


@router.get("/disasters/{disaster_id}")
def get_disaster(disaster_id: int, db: Session = Depends(get_db)):
    """Retrieve details and response tasks for a specific disaster."""
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster record not found.")

    return {
        "id": disaster.id,
        "title": disaster.title,
        "disaster_type": disaster.disaster_type,
        "description": disaster.description,
        "district": disaster.district,
        "place": disaster.place,
        "severity": disaster.severity,
        "status": disaster.status,
        "created_at": disaster.created_at.isoformat() if disaster.created_at else None,
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "location": t.location,
                "urgency": t.urgency,
                "status": t.status,
                "skills_required": t.skills_required,
                "required_volunteers": t.required_volunteer_count,
                "assigned_volunteers": len(t.assignments) if t.assignments else 0,
            }
            for t in disaster.tasks
        ],
    }


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    """Retrieve all emergency response tasks."""
    tasks = db.query(Task).order_by(Task.id.desc()).all()
    return [
        {
            "id": t.id,
            "disaster_id": t.disaster_id,
            "title": t.title,
            "description": t.description,
            "location": t.location,
            "urgency": t.urgency,
            "status": t.status,
            "required_volunteers": t.required_volunteer_count,
            "skills_required": t.skills_required,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single response task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return {
        "id": task.id,
        "disaster_id": task.disaster_id,
        "title": task.title,
        "description": task.description,
        "location": task.location,
        "urgency": task.urgency,
        "status": task.status,
        "required_volunteers": task.required_volunteer_count,
        "skills_required": task.skills_required,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


@router.get("/volunteers")
def list_volunteers(db: Session = Depends(get_db)):
    """Public list of active approved volunteers with sanitized details."""
    volunteers = (
        db.query(User)
        .filter(User.role == "volunteer", User.is_approved.is_(True))
        .order_by(User.id.desc())
        .all()
    )
    return [
        {
            "id": v.id,
            "first_name": v.first_name,
            "last_name": v.last_name,
            "district": v.district,
            "place": v.place,
            "skills": [s for s in [v.skill1, v.skill2, v.skill3] if s],
            "experience_years": v.years_experience or 0,
            "profile_image": v.profile_image,
        }
        for v in volunteers
    ]
