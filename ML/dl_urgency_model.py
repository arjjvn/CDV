"""
DL part of the Community Disaster Volunteer Hub
-----------------------------------------------
The coordinator fills TWO fields:
    1) Location  -> chosen from a drop-down list (handled in hub_pipeline.py)
    2) Message   -> free text, e.g. "there is a medical emergency, need volunteers"
                                    "there is a flood"

This file reads the MESSAGE and predicts 3 things with neural networks:
    skill     -> Medical / Rescue / Ambulance / Driving / Food Supply / Unknown
    urgency   -> high / medium / low        (medium when nothing is said)
    disaster  -> flood / landslide / fire / accident / Unknown

Run (training):   python dl_urgency_model.py
"""
import os
import random
import warnings

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import FeatureUnion

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "dl_urgency_model.joblib")
FIELDS = ["skill", "urgency", "disaster"]

# ----------------------------------------------------------------------
# 1) WORDS THE SYSTEM SHOULD UNDERSTAND (edit freely to add more)
# ----------------------------------------------------------------------
SKILL_WORDS = {
    "Medical": ["medical", "doctor", "nurse", "first aid", "medical help",
                "medical team", "triage", "paramedic", "medicine"],
    "Rescue": ["rescue", "rescue team", "boat rescue", "search and rescue",
               "people trapped", "stranded families", "divers", "boat"],
    "Ambulance": ["ambulance", "casualty transport", "ambulance for injured",
                  "patient transport", "critical casualty transport"],
    "Driving": ["driver", "driving", "vehicle", "transport vehicle",
                "truck driver", "supply transport"],
    "Food Supply": ["food", "food supply", "meals", "relief camp food",
                    "food packets", "cooked food", "food and drinking water"],
}
URGENCY_WORDS = {
    "high": ["urgent", "urgently", "immediately", "critical", "asap",
             "very urgent", "emergency", "right now"],
    "medium": ["soon", "within a few hours", "today", "needed today",
               "moderate priority"],
    "low": ["no rush", "tomorrow", "low priority", "when possible", "no hurry"],
}
DISASTER_WORDS = {
    "flood": ["flood", "flooding", "flood water", "water level rising"],
    "landslide": ["landslide", "landslip", "mudslide"],
    "fire": ["fire", "building fire", "fire accident"],
    "accident": ["road accident", "accident", "bus accident", "collision"],
}

SKILL_FRAGMENTS = ["need {w}", "we need {w}", "please send {w}", "{w} required",
                   "{w} needed", "send {w}", "need volunteers with {w}",
                   "i need {w}", "require {w}"]
DISASTER_FRAGMENTS = ["there is a {w}", "{w} here", "due to {w}", "{w} situation",
                      "{w} victims", "after the {w}", "{w} reported", "there is {w}"]
URGENCY_FRAGMENTS = ["{w}", "this is {w}"]
# "there is a medical emergency" -> always counts as HIGH urgency
EMERGENCY_FRAGMENTS = ["there is a {w} {e}", "{w} {e}", "i need {w}, there is a {w} {e}"]
FILLERS = ["need volunteers", "volunteers needed", "please help",
           "people affected", "send volunteers", "need help"]
NOISE = ["hello", "test", "ok", "kollam", "hi", "help", "volunteers needed",
         "please", "thanks", "asdf", "123"]


# ----------------------------------------------------------------------
# 2) CREATE TRAINING MESSAGES (you have no message dataset yet, so we
#    generate realistic examples automatically)
# ----------------------------------------------------------------------
def _add_typo(text):
    words = text.split(" ")
    idx = random.randrange(len(words))
    w = words[idx]
    if len(w) > 4:
        pos = random.randrange(1, len(w) - 1)
        if random.random() < 0.5:
            w = w[:pos] + w[pos + 1:]                        # drop a letter
        else:
            w = w[:pos] + w[pos + 1] + w[pos] + w[pos + 2:]  # swap two letters
        words[idx] = w
    return " ".join(words)


def _random_case(text):
    r = random.random()
    if r < 0.3:
        return text.lower()
    if r < 0.4:
        return text.upper()
    return text


def build_training_data(n_samples=8000, seed=42):
    random.seed(seed)
    texts, labels = [], []
    for _ in range(n_samples):
        if random.random() < 0.05:                      # meaningless message
            text = random.choice(NOISE)
            label = {"skill": "Unknown", "urgency": "medium", "disaster": "Unknown"}
        else:
            skill = random.choice(list(SKILL_WORDS)) if random.random() > 0.20 else "Unknown"
            dis = random.choice(list(DISASTER_WORDS)) if random.random() > 0.25 else "Unknown"
            skill_w = random.choice(SKILL_WORDS[skill]) if skill != "Unknown" else ""
            dis_w = random.choice(DISASTER_WORDS[dis]) if dis != "Unknown" else ""
            urg_label = "medium"                        # default if nothing is said
            parts = []
            structured = random.random() < 0.3

            if skill != "Unknown" and not structured and random.random() < 0.25:
                parts.append(random.choice(EMERGENCY_FRAGMENTS).format(
                    w=skill_w, e=random.choice(["emergency", "urgency"])))
                urg_label = "high"
            else:
                urg = random.choice(list(URGENCY_WORDS))
                urg_w = random.choice(URGENCY_WORDS[urg])
                say_urgency = random.random() < 0.7
                if structured:
                    if dis != "Unknown":
                        parts.append(f"disaster;{dis_w}")
                    if skill != "Unknown":
                        parts.append(f"task;{skill_w}")
                    if say_urgency:
                        parts.append(f"urgency;{urg}")
                        urg_label = urg
                else:
                    if skill != "Unknown":
                        parts.append(random.choice(SKILL_FRAGMENTS).format(w=skill_w))
                    if say_urgency:
                        parts.append(random.choice(URGENCY_FRAGMENTS).format(w=urg_w))
                        urg_label = urg
            if not structured and dis != "Unknown":
                parts.append(random.choice(DISASTER_FRAGMENTS).format(w=dis_w))
            if not structured and random.random() < 0.4:
                parts.append(random.choice(FILLERS))
            if not parts:
                parts = [random.choice(FILLERS)]

            if structured:
                random.shuffle(parts)
                text = ", ".join(parts)
            else:
                random.shuffle(parts)
                text = random.choice([", ", " - ", ". ", " "]).join(parts)
            label = {"skill": skill, "urgency": urg_label, "disaster": dis}

        text = _random_case(text)
        if random.random() < 0.3:
            text = _add_typo(text)
        texts.append(text)
        labels.append(label)
    return texts, labels


# ----------------------------------------------------------------------
# 3) TRAIN THE NEURAL NETWORKS
# ----------------------------------------------------------------------
def make_vectorizer():
    # words + letter-groups: letter-groups let the model survive typos
    return FeatureUnion([
        ("words", TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                                  lowercase=True, token_pattern=r"[A-Za-z]+")),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5),
                                  lowercase=True)),
    ])


def train_and_save():
    texts, labels = build_training_data()
    idx_train, idx_test = train_test_split(
        np.arange(len(texts)), test_size=0.2, random_state=42)

    train_texts = [texts[i] for i in idx_train]
    test_texts = [texts[i] for i in idx_test]

    vectorizer = make_vectorizer()
    X_train = vectorizer.fit_transform(train_texts)
    X_test = vectorizer.transform(test_texts)

    models = {}
    class_names = {}
    for field in FIELDS:
        names = sorted({lab[field] for lab in labels})
        class_names[field] = names
        # networks work with numbers, so label 'Medical' becomes e.g. 3
        y_train = np.array([names.index(labels[i][field]) for i in idx_train])
        y_test = np.array([names.index(labels[i][field]) for i in idx_test])
        net = MLPClassifier(hidden_layer_sizes=(128, 64), activation="relu",
                            max_iter=300, early_stopping=True,
                            random_state=42)
        net.fit(X_train, y_train)
        acc = accuracy_score(y_test, net.predict(X_test))
        print(f"{field:9s} accuracy on held-out messages: {acc:.3f}")
        models[field] = net

    joblib.dump({"vectorizer": vectorizer, "models": models,
                 "class_names": class_names}, MODEL_PATH)
    print("Saved:", MODEL_PATH)


# ----------------------------------------------------------------------
# 4) USE THE TRAINED NETWORKS
# ----------------------------------------------------------------------
_BUNDLE = None


def understand_message(text):
    """Return {'skill':..., 'skill_conf':..., 'urgency':..., 'disaster':..., ...}."""
    global _BUNDLE
    if _BUNDLE is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "dl_urgency_model.joblib not found. Run: python dl_urgency_model.py")
        _BUNDLE = joblib.load(MODEL_PATH)

    X = _BUNDLE["vectorizer"].transform([text])
    result = {}
    for field in FIELDS:
        net = _BUNDLE["models"][field]
        proba = net.predict_proba(X)[0]
        best = int(np.argmax(proba))
        result[field] = _BUNDLE["class_names"][field][int(net.classes_[best])]
        result[field + "_conf"] = round(float(proba[best]), 3)
    return result


if __name__ == "__main__":
    train_and_save()
    print("\nQuick test on messages the network has never seen:")
    tests = [
        "there is a medical emergency need volunteers",
        "there is a flood",
        "i need a medical team there is a medical urgency",
        "boat needed urgent! people stranded, flood",
        "ambulance for injured, bus collision, critical",
        "need a driver tomorrow",
        "disaster;landslide, task;rescue, urgency;medium",
        "need food packets, no hurry",
        "there is a fire in the building",
        "kollam",
    ]
    for t in tests:
        r = understand_message(t)
        print(f"\n> {t}")
        print(f"  skill={r['skill']} ({r['skill_conf']}), urgency={r['urgency']} "
              f"({r['urgency_conf']}), disaster={r['disaster']} ({r['disaster_conf']})")