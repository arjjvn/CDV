
import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

CSV_PATH = "disaster_volunteer_dataset.csv"
SKILL_COLS = ["Skill_1", "Skill_2", "Skill_3"]

NUMERIC_FEATURES = ["Distance_km", "Exp_Years", "Skill_Match",
                    "Skill_Rank", "Shift_Start_Hour"]
CATEGORICAL_FEATURES = ["Required_Skill"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# ----------------------------------------------------------------------
# STEP 1: LOAD + HANDLE MISSING VALUES
# ----------------------------------------------------------------------
def load_and_clean(path=CSV_PATH):
    df = pd.read_csv(path)

    # Missing experience -> median (a "typical" volunteer)
    exp_median = df["Exp_Years"].median()
    df["Exp_Years"] = df["Exp_Years"].fillna(exp_median)

    # Missing text fields -> an explicit label instead of NaN
    df["Skill_2"] = df["Skill_2"].fillna("None")
    df["Skill_3"] = df["Skill_3"].fillna("None")
    df["Available_Time_Period"] = df["Available_Time_Period"].fillna("Unknown")

    return df, exp_median


# ----------------------------------------------------------------------
# STEP 2: FEATURE ENGINEERING + ENCODING
# ----------------------------------------------------------------------
def add_skill_features(df, required_skill_col="Required_Skill"):
    """Create Skill_Match and Skill_Rank from the volunteer's 3 skills."""
    req = df[required_skill_col]
    df["Skill_Match"] = df[SKILL_COLS].eq(req, axis=0).any(axis=1).astype(int)
    # 1 = primary skill, 2 = second, 3 = third, 0 = not a skill they have
    df["Skill_Rank"] = np.select(
        [df["Skill_1"] == req, df["Skill_2"] == req, df["Skill_3"] == req],
        [1, 2, 3], default=0)
    return df


def add_shift_hour(df):
    """'22:00 - 06:00' -> 22 ; 'Unknown' -> -1 (a number the model can use)."""
    start = df["Available_Time_Period"].str.split(" - ").str[0].str[:2]
    df["Shift_Start_Hour"] = pd.to_numeric(start, errors="coerce").fillna(-1)
    return df


def build_preprocessor():
    # Numbers pass through untouched (Random Forest needs no scaling).
    # Text categories are turned into 0/1 columns (one-hot encoding).
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ("num", "passthrough", NUMERIC_FEATURES),
    ])


# ----------------------------------------------------------------------
# STEP 3 + 4: SPLIT, TRAIN, EVALUATE, SAVE
# ----------------------------------------------------------------------
def train_and_save():
    df, exp_median = load_and_clean()
    df = add_skill_features(df)
    df = add_shift_hour(df)

    X = df[ALL_FEATURES]
    y = df["Suitability_Label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    preprocessor = build_preprocessor()
    X_train_enc = preprocessor.fit_transform(X_train)   # learn on TRAIN only
    X_test_enc = preprocessor.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200, max_depth=12, min_samples_leaf=5,
        random_state=42, n_jobs=-1)
    model.fit(X_train_enc, y_train)

    pred = model.predict(X_test_enc)
    print("Test accuracy:", round(accuracy_score(y_test, pred), 4))
    print(classification_report(y_test, pred, target_names=["Not suitable", "Suitable"]))

    names = preprocessor.get_feature_names_out()
    imp = pd.Series(model.feature_importances_, index=names).sort_values(ascending=False)
    print("Top feature importances:\n", imp.head(6).round(3))

    joblib.dump(model, "volunteer_model.joblib")
    joblib.dump(preprocessor, "volunteer_preprocessor.joblib")
    joblib.dump({"exp_median": exp_median}, "volunteer_fill_values.joblib")
    print("Saved: volunteer_model.joblib, volunteer_preprocessor.joblib, volunteer_fill_values.joblib")


# ----------------------------------------------------------------------
# STEP 5: RECOMMENDATION FUNCTION
# ----------------------------------------------------------------------
def recommend_volunteers(task_requirements, top_n=5, csv_path=CSV_PATH):
    """
    task_requirements example:
        {"Required_Skill": "Medical", "City": "Chengannur", "Max_Distance": 10}
    Optional keys: "Min_Experience" (years)
    """
    model = joblib.load("volunteer_model.joblib")
    preprocessor = joblib.load("volunteer_preprocessor.joblib")
    fills = joblib.load("volunteer_fill_values.joblib")

    # 1) Load + clean with the SAME rules used in training
    df = pd.read_csv(csv_path)
    df["Exp_Years"] = df["Exp_Years"].fillna(fills["exp_median"])
    df["Skill_2"] = df["Skill_2"].fillna("None")
    df["Skill_3"] = df["Skill_3"].fillna("None")
    df["Available_Time_Period"] = df["Available_Time_Period"].fillna("Unknown")

    # 2) Apply the coordinator's task to every candidate
    df["Required_Skill"] = task_requirements["Required_Skill"]
    df = add_skill_features(df)
    df = add_shift_hour(df)

    # 3) Hard filters (cheap rules first)
    mask = df["Skill_Match"] == 1                              # must have the skill
    if task_requirements.get("City"):
        mask &= df["City"].str.lower() == task_requirements["City"].lower()
    if task_requirements.get("Max_Distance") is not None:
        mask &= df["Distance_km"] <= task_requirements["Max_Distance"]
    if task_requirements.get("Min_Experience") is not None:
        mask &= df["Exp_Years"] >= task_requirements["Min_Experience"]
    candidates = df[mask].copy()

    if candidates.empty:
        print("No volunteers match these requirements. Try a larger distance.")
        return candidates

    # 4) ML scoring: probability of class 1 (= Suitable)
    X_enc = preprocessor.transform(candidates[ALL_FEATURES])
    candidates["Match_Score"] = (model.predict_proba(X_enc)[:, 1] * 100).round(1)

    # 5) Rank and tidy up
    candidates["Name"] = candidates["First_Name"] + " " + candidates["Last_Name"]
    candidates = candidates.sort_values(
        ["Match_Score", "Distance_km"], ascending=[False, True])
    cols = ["Match_ID", "Name", "City", "Distance_km", "Exp_Years",
            "Available_Time_Period", "Match_Score"]
    result = candidates[cols].head(top_n).reset_index(drop=True)
    result.index += 1
    return result


if __name__ == "__main__":
    train_and_save()
    task = {"Required_Skill": "Medical", "City": "Chengannur", "Max_Distance": 10}
    top = recommend_volunteers(task, top_n=5)
    print("\nTop volunteers for", task)
    print(top.to_string())
    for _, r in top.iterrows():
        print(f"{r['Name']} - {r['Match_Score']:.1f}% match")