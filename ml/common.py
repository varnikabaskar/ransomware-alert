from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

BEHAVIORAL_MODEL_PATH = MODEL_DIR / "behavioral_uades.joblib"
DECOY_MODEL_PATH = MODEL_DIR / "decoy_rf.joblib"
