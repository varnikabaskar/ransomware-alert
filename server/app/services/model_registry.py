from pathlib import Path

import joblib


class ModelRegistry:
    def __init__(self, model_dir: str) -> None:
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.behavioral_model = None
        self.decoy_model = None

    def load(self) -> None:
        behavioral_path = self.model_dir / "behavioral_uades.joblib"
        decoy_path = self.model_dir / "decoy_rf.joblib"

        self.behavioral_model = joblib.load(behavioral_path) if behavioral_path.exists() else None
        self.decoy_model = joblib.load(decoy_path) if decoy_path.exists() else None

    def has_models(self) -> bool:
        return self.behavioral_model is not None and self.decoy_model is not None
