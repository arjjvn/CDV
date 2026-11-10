from pathlib import Path
from functools import lru_cache
import logging
import warnings

warnings.filterwarnings("ignore")

import joblib
import numpy as np
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# PATH CONFIGURATION
# ----------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_DIR / "ML and DL"
DL_MODEL_PATH = MODEL_DIR / "dl_urgency_model.joblib"
FIELDS = ["skill", "urgency", "disaster"]

_BUNDLE = None


# ----------------------------------------------------------------------
# MODEL LOADER
# ----------------------------------------------------------------------

def load_dl_model():
    """Load the trained multi-head neural network bundle."""
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE

    if not DL_MODEL_PATH.exists():
        raise FileNotFoundError(f"DL Urgency Model not found at: {DL_MODEL_PATH}")

    _BUNDLE = joblib.load(DL_MODEL_PATH)
    logger.info("Deep Learning Urgency Model loaded successfully from %s", DL_MODEL_PATH)
    return _BUNDLE


# ----------------------------------------------------------------------
# SYNCHRONOUS INFERENCE
# ----------------------------------------------------------------------

def understand_message_sync(text: str) -> dict:
    """
    Process incoming distress text using the Deep Learning MLP neural network.
    Returns:
        {
            'skill': str,
            'skill_conf': float,
            'urgency': str,
            'urgency_conf': float,
            'disaster': str,
            'disaster_conf': float,
            'is_emergency': bool
        }
    """
    if not text or not str(text).strip():
        return {
            "skill": "Unknown",
            "skill_conf": 0.0,
            "urgency": "low",
            "urgency_conf": 0.0,
            "disaster": "Unknown",
            "disaster_conf": 0.0,
            "is_emergency": False,
        }

    bundle = load_dl_model()
    vectorizer = bundle["vectorizer"]
    models = bundle["models"]
    class_names = bundle["class_names"]

    X = vectorizer.transform([str(text)])
    result = {}

    for field in FIELDS:
        net = models[field]
        proba = net.predict_proba(X)[0]
        best_idx = int(np.argmax(proba))
        class_label = class_names[field][int(net.classes_[best_idx])]
        conf = float(proba[best_idx])

        result[field] = class_label
        result[field + "_conf"] = round(conf, 3)

    # Determine if message signals an active emergency
    urgency_val = result.get("urgency", "low").lower()
    is_high_urgency = urgency_val in ("high", "urgent", "critical")
    has_recognized_disaster = result.get("disaster", "Unknown") != "Unknown"
    has_recognized_skill = result.get("skill", "Unknown") != "Unknown"

    result["is_emergency"] = is_high_urgency or (has_recognized_disaster and has_recognized_skill)
    return result


# ----------------------------------------------------------------------
# ASYNCHRONOUS PUBLIC INTERFACE
# ----------------------------------------------------------------------

async def analyze_emergency_message(text: str) -> dict:
    """Asynchronous wrapper for threadpool execution."""
    return await run_in_threadpool(understand_message_sync, text)
