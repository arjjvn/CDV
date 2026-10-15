"""
Community Disaster Volunteer Hub - full pipeline
    Location (drop-down) + Message (text) --(DL)--> task --(ML)--> ranked volunteers

Run:  python hub_pipeline.py
(Before the first run, run volunteer_matcher.py and dl_urgency_model.py once.)
"""
import os

# Always work inside this file's own folder, so the CSV and .joblib files are found
os.chdir(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_FILES = ["disaster_volunteer_dataset.csv", "volunteer_model.joblib",
                  "volunteer_preprocessor.joblib", "volunteer_fill_values.joblib",
                  "dl_urgency_model.joblib"]
_missing = [f for f in REQUIRED_FILES if not os.path.exists(f)]
if _missing:
    raise SystemExit(
        "Missing files: " + ", ".join(_missing) + "\n"
        "Run these first, in order:\n"
        "  1) python volunteer_matcher.py   (trains the ML model)\n"
        "  2) python dl_urgency_model.py    (trains the DL model)\n"
        "Also keep disaster_volunteer_dataset.csv in this same folder.")

from dl_urgency_model import understand_message      # DL part
from volunteer_matcher import recommend_volunteers   # ML part

# The location drop-down list (the 10 cities in your dataset)
CITIES = ["Alappuzha", "Chengannur", "Edappally", "Kakkanad", "Kochi",
          "Kollam", "Kottayam", "Kozhikode", "Thiruvananthapuram", "Thrissur"]

# If the message names a disaster but no skill ("there is a flood"),
# this skill is assumed. Change it to suit your project.
DEFAULT_SKILL_BY_DISASTER = {
    "flood": "Rescue",
    "landslide": "Rescue",
    "fire": "Rescue",
    "accident": "Ambulance",
}

# How urgency changes the search. Change these numbers to suit your project.
URGENCY_RULES = {
    "high":   {"Max_Distance": 15, "Min_Experience": 3},   # strict: close and experienced
    "medium": {"Max_Distance": 25, "Min_Experience": 1},
    "low":    {"Max_Distance": 45, "Min_Experience": 0},   # relaxed: anyone available
}
MIN_CONFIDENCE = 0.50           # below this the DL model is too unsure


def handle_urgency_message(text, city, top_n=3):
    """
    text = the message typed in the text box
    city = the location chosen in the drop-down (one of CITIES)
    Returns a dictionary with everything that happened.
    """
    # ---- Field 1: location from the drop-down ---------------------------------
    matches = [c for c in CITIES if c.lower() == str(city).strip().lower()]
    if not matches:
        return {"ok": False, "parsed": {}, "message": "Please choose a location from the list."}
    city = matches[0]

    if not text or not text.strip():
        return {"ok": False, "parsed": {}, "message": "Please type the emergency message."}

    # ---- Field 2: DL understands the message ---------------------------------
    parsed = understand_message(text)
    skill, notes = parsed["skill"], []

    if skill == "Unknown" or parsed["skill_conf"] < MIN_CONFIDENCE:
        disaster = parsed["disaster"]
        if disaster in DEFAULT_SKILL_BY_DISASTER and parsed["disaster_conf"] >= MIN_CONFIDENCE:
            skill = DEFAULT_SKILL_BY_DISASTER[disaster]
            notes.append(f"No skill was mentioned, so {skill} was assumed for the {disaster}.")
        else:
            return {"ok": False, "parsed": parsed,
                    "message": "I could not understand the emergency. Please mention what is "
                               "needed (doctor, rescue, ambulance, driver, food) or the "
                               "disaster (flood, landslide, fire, accident)."}

    # ---- Bridge: DL output -> ML input ---------------------------------------
    rules = URGENCY_RULES[parsed["urgency"]]
    task = {
        "Required_Skill": skill,
        "City": city,
        "Max_Distance": rules["Max_Distance"],
        "Min_Experience": rules["Min_Experience"],
    }

    # ---- ML: rank volunteers --------------------------------------------------
    result = recommend_volunteers(task, top_n=top_n)
    if result.empty:                      # nobody found: widen the search once
        task["Max_Distance"] = 45
        task["Min_Experience"] = 0
        result = recommend_volunteers(task, top_n=top_n)
        notes.append("No exact match, so the search was widened to 45 km and any experience.")

    return {"ok": not result.empty, "parsed": parsed, "task": task,
            "volunteers": result, "message": " ".join(notes)}


def show(text, city):
    print("=" * 70)
    print("LOCATION:", city)
    print("MESSAGE :", text)
    out = handle_urgency_message(text, city)
    p = out["parsed"]
    if p:
        print(f"DL understood -> skill={p['skill']}, urgency={p['urgency']}, "
              f"disaster={p['disaster']}")
    if "task" in out:
        print("Sent to ML    ->", out["task"])
    if out["message"]:
        print("NOTE:", out["message"])
    if out["ok"]:
        print("\nTop volunteers:")
        for rank, (_, r) in enumerate(out["volunteers"].iterrows(), start=1):
            print(f"  {rank}. {r['Name']} (ID {r['Match_ID']}) - {r['Match_Score']:.1f}% match, "
                  f"{r['Distance_km']} km away, {r['Exp_Years']:.0f} yrs experience")


if __name__ == "__main__":
    show("there is a medical emergency need volunteers", "Chengannur")
    show("there is a flood", "Alappuzha")
    show("need food packets, no hurry", "Kollam")
    show("kollam", "Kochi")          # meaningless message -> asks again