from pathlib import Path
from datetime import datetime, time
from functools import lru_cache
import re

import joblib
import pandas as pd

from starlette.concurrency import run_in_threadpool



PROJECT_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = PROJECT_DIR / "ML and DL"

MODEL_PATH = MODEL_DIR / "volunteer_model.joblib"
PREPROCESSOR_PATH = MODEL_DIR / "volunteer_preprocessor.joblib"


MATCH_FEATURES = [
    "Exp_Years",
    "Skill_Match",
    "Skill_Rank",
    "Total_Skills",
    "Shift_Start_Hour",
    "Shift_Duration",
    "Required_Skill"
]



SKILL_ALIASES = {
    "first aid": "Medical",
    "cpr": "Medical",
    "triage": "Medical",
    "medical": "Medical",
    "doctor": "Medical",
    "nurse": "Medical",
    "nursing": "Medical",
    "paramedic": "Medical",
    "healthcare": "Medical",
    "ambulance": "Ambulance",
    "driver": "Driving",
    "driving": "Driving",
    "food supply": "Food Supply",
    "food distribution": "Food Supply",
    "logistics": "Food Supply",
    "cooking": "Food Supply",
    "general relief": "Food Supply",
    "rescue": "Rescue",
    "swimming": "Rescue",
    "navigation": "Rescue",
    "search and rescue": "Rescue",
    "search & river bank rescue": "Rescue",
    "boat": "Rescue",
    "fire": "Rescue",
    "lifeguard": "Rescue",
}


@lru_cache(maxsize=1)
def load_volunteer_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    if not PREPROCESSOR_PATH.exists():
        raise FileNotFoundError(f"Preprocessor not found: {PREPROCESSOR_PATH}")

    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)

    return model, preprocessor


def resolve_category(value, categories, aliases=None):

    if not value:
        return None

    value = str(value).strip()

    # First try exact category matching
    for category in categories:
        if str(category).strip().casefold() == value.casefold():
            return str(category)

    # Then try aliases
    if aliases:
        alias = aliases.get(value.casefold())
        if alias:
            for category in categories:
                if str(category).strip().casefold() == alias.casefold():
                    return str(category)

    return None


def get_volunteer_city(volunteer):
    
    # Since the ML model no longer uses City, we just resolve it locally
    locations = [
        volunteer.get("place"),
        volunteer.get("district"),
        volunteer.get("address")
    ]
    
    for loc in locations:
        if loc and str(loc).strip():
            return str(loc).strip()
            
    return None




def parse_shift_times(from_val, to_val=None):
    if not from_val and not to_val:
        return 9, 8

    start_hour, end_hour = -1, -1

    if hasattr(from_val, "hour"):
        start_hour = from_val.hour
    elif from_val:
        v_str = str(from_val).strip()
        if " - " in v_str:
            parts = v_str.split(" - ")
            try:
                start_hour = int(parts[0][:2])
                end_hour = int(parts[1][:2])
            except (ValueError, IndexError):
                pass
        else:
            try:
                start_hour = int(v_str[:2])
            except (ValueError, IndexError):
                pass

    if to_val is not None and end_hour == -1:
        if hasattr(to_val, "hour"):
            end_hour = to_val.hour
        elif to_val:
            try:
                end_hour = int(str(to_val).strip()[:2])
            except (ValueError, IndexError):
                pass

    if start_hour == -1:
        start_hour = 9
    if end_hour == -1:
        end_hour = (start_hour + 8) % 24

    duration = end_hour - start_hour
    if duration <= 0:
        duration += 24

    return start_hour, duration


def find_matches_sync(
    task_data,
    volunteer_data,
    requested_city,
    top_n
):

    model, preprocessor = load_volunteer_model()

    encoder = preprocessor.named_transformers_["cat"]
    
    skill_categories = encoder.categories_[0]

    task_city = requested_city

    raw_skills = re.split(
        r"[,;|\n]+",
        task_data["skills_required"]
    )

    required_skills = []
    for raw_skill in raw_skills:
        skill = resolve_category(
            raw_skill,
            skill_categories,
            SKILL_ALIASES
        )
        if skill and skill not in required_skills:
            required_skills.append(skill)

    if not required_skills:
        return {
            "city": task_city,
            "matches": [],
            "message": "No recognized task skills found."
        }

    feature_rows = []
    volunteer_info = []

    city_matched = False
    if requested_city and requested_city.strip():
        req_clean = requested_city.strip().casefold()
        city_filtered = [
            v for v in volunteer_data
            if req_clean in (get_volunteer_city(v) or "").casefold()
        ]
        if city_filtered:
            volunteer_data = city_filtered
            city_matched = True

    for volunteer in volunteer_data:

        city = get_volunteer_city(volunteer)

        raw_exp = volunteer.get("experience")
        try:
            experience = float(raw_exp) if raw_exp is not None else 0.0
        except (TypeError, ValueError):
            experience = 0.0
            
        raw_volunteer_skills = [
            volunteer.get("skill1"), 
            volunteer.get("skill2"), 
            volunteer.get("skill3")
        ]
        
        total_skills = sum(
            1 for s in raw_volunteer_skills 
            if s and str(s).strip().casefold() != "none"
        )

        profile_skills = [
            resolve_category(s, skill_categories, SKILL_ALIASES)
            for s in raw_volunteer_skills
        ]

        available_from = volunteer.get("available_from")
        available_to = volunteer.get("available_to")
        shift_hour, shift_duration = parse_shift_times(available_from, available_to)

        for required_skill in required_skills:
            skill_rank = 0

            for rank, profile_skill in enumerate(profile_skills, start=1):
                if profile_skill == required_skill:
                    skill_rank = rank
                    break

            if skill_rank == 0:
                continue

            feature_rows.append({
                "Exp_Years": experience,
                "Skill_Match": 1,
                "Skill_Rank": skill_rank,
                "Total_Skills": total_skills,
                "Shift_Start_Hour": shift_hour,
                "Shift_Duration": shift_duration,
                "Required_Skill": required_skill
            })

            volunteer_info.append({
                "id": volunteer["id"],
                "name": (f"{volunteer['first_name']} {volunteer['last_name']}").strip(),
                "city": city,
                "experience": experience,
                "available_from": str(available_from) if available_from is not None else None,
                "skill": required_skill
            })

    if not feature_rows:
        return {
            "city": task_city,
            "matches": [],
            "message": "No volunteers found with the required skills."
        }


    X = pd.DataFrame(feature_rows, columns=MATCH_FEATURES)
    X_encoded = preprocessor.transform(X)
    classes = list(model.classes_)

    suitable_index = next(
        (
            index for index, label in enumerate(classes)
            if (label == 1 or str(label).strip().casefold() in ("1", "true", "suitable", "yes"))
        ),
        None
    )

    if suitable_index is None:
        raise ValueError("Suitable class (1) is missing from the trained model.")

    scores = (model.predict_proba(X_encoded)[:, suitable_index] * 100)

    grouped = {}

    for info, score in zip(volunteer_info, scores):
        volunteer_id = info["id"]

        if volunteer_id not in grouped:
            grouped[volunteer_id] = {
                "id": volunteer_id,
                "name": info["name"],
                "city": info["city"],
                "experience": info["experience"],
                "available_from": info["available_from"],
                "matched_skills": [],
                "scores": []
            }

        grouped[volunteer_id]["scores"].append(float(score))

        if info["skill"] not in grouped[volunteer_id]["matched_skills"]:
            grouped[volunteer_id]["matched_skills"].append(info["skill"])

   
    results = []

    for volunteer in grouped.values():
        prediction_scores = volunteer.pop("scores")
        volunteer["match_score"] = round(
            sum(prediction_scores) / len(prediction_scores), 1
        )
        results.append(volunteer)

    results.sort(
        key=lambda item: (item["match_score"], item["experience"]),
        reverse=True
    )

    return {
        "city": task_city,
        "matches": results[:top_n],
        "message": "Volunteer matching completed successfully."
    }


async def find_volunteer_matches(
    task,
    volunteers,
    city=None,
    top_n=5
):

    volunteer_data = [
        {
            "id": volunteer.id,
            "first_name": volunteer.first_name or "",
            "last_name": volunteer.last_name or "",
            "skill1": volunteer.skill1,
            "skill2": volunteer.skill2,
            "skill3": volunteer.skill3,
            "place": getattr(volunteer, "place", None),
            "district": getattr(volunteer, "district", None),
            "address": getattr(volunteer, "address", None),
            "experience": getattr(volunteer, "years_experience", None),
            "available_from": getattr(volunteer, "available_from", None),
            "available_to": getattr(volunteer, "available_to", None)
        }
        for volunteer in volunteers
    ]

    task_data = {
        "skills_required": task.skills_required or "",
        "location": task.location or ""
    }

    return await run_in_threadpool(
        find_matches_sync,
        task_data,
        volunteer_data,
        city,
        max(1, min(int(top_n), 50))
    )