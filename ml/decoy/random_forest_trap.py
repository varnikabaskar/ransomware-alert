from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestClassifier


@dataclass
class DecoyRFConfig:
    n_estimators: int = 400
    random_state: int = 42
    class_weight: str = "balanced"
    max_depth: int | None = 20
    min_samples_split: int = 4
    min_samples_leaf: int = 2
    max_features: str = "sqrt"


class DecoyRFModel:
    def __init__(self, config: DecoyRFConfig | None = None) -> None:
        self.config = config or DecoyRFConfig()
        self.decision_threshold: float = 0.5
        self.model = RandomForestClassifier(
            n_estimators=self.config.n_estimators,
            random_state=self.config.random_state,
            class_weight=self.config.class_weight,
            max_depth=self.config.max_depth,
            min_samples_split=self.config.min_samples_split,
            min_samples_leaf=self.config.min_samples_leaf,
            max_features=self.config.max_features,
            n_jobs=-1,
        )

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(x, y)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(x)

    def set_decision_threshold(self, threshold: float) -> None:
        self.decision_threshold = float(np.clip(threshold, 0.05, 0.95))
