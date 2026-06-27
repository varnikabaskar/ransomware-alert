import copy
from dataclasses import dataclass

import numpy as np
from sklearn.metrics import log_loss
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler


@dataclass
class UADESConfig:
    random_state: int = 42
    ensemble_size: int = 5
    hidden_layer_sizes: tuple[tuple[int, ...], ...] = ((64, 32), (96, 48), (128, 64))
    epochs: int = 60
    min_epochs: int = 10
    epoch_patience: int = 8
    validation_split: float = 0.2
    patience: int = 2


class UADESBehavioralModel:
    def __init__(self, config: UADESConfig | None = None) -> None:
        self.config = config or UADESConfig()
        self.scaler = StandardScaler()
        self.models: list[MLPClassifier] = []
        self.sequence_length: int = 20
        self.vector_dim: int = 0
        self.decision_threshold: float = 0.5
        self.selected_feature_indices: list[int] = []

    @staticmethod
    def _safe_log_loss(y_true: np.ndarray, y_prob: np.ndarray) -> float:
        labels = np.unique(y_true)
        if len(labels) < 2:
            pred = (y_prob[:, 1] >= 0.5).astype(int)
            return float(np.mean(pred != y_true))
        return float(log_loss(y_true, y_prob, labels=[0, 1]))

    def _fit_model_by_epochs(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_val: np.ndarray,
        y_val: np.ndarray,
        arch: tuple[int, ...],
        seed: int,
    ) -> tuple[MLPClassifier, float, int]:
        model = MLPClassifier(
            hidden_layer_sizes=arch,
            random_state=seed,
            max_iter=1,
            warm_start=True,
            early_stopping=False,
            shuffle=True,
        )

        best_model: MLPClassifier | None = None
        best_loss = float("inf")
        bad_epochs = 0
        epochs_ran = 0

        for epoch in range(1, self.config.epochs + 1):
            model.fit(x_train, y_train)
            prob = model.predict_proba(x_val)
            loss = self._safe_log_loss(y_val, prob)
            epochs_ran = epoch

            if loss < best_loss:
                best_loss = loss
                bad_epochs = 0
                best_model = copy.deepcopy(model)
            else:
                bad_epochs += 1

            if epoch >= self.config.min_epochs and bad_epochs >= self.config.epoch_patience:
                break

        return (best_model or model), float(best_loss), int(epochs_ran)

    @staticmethod
    def _pick_threshold(
        y_true: np.ndarray,
        probs: np.ndarray,
        max_fpr: float = 0.03,
        min_acc: float = 0.97,
    ) -> tuple[float, float, float]:
        best = None
        for thr in np.linspace(0.05, 0.95, 181):
            pred = (probs >= thr).astype(int)
            tp = float(np.sum((pred == 1) & (y_true == 1)))
            fp = float(np.sum((pred == 1) & (y_true == 0)))
            tn = float(np.sum((pred == 0) & (y_true == 0)))
            fpr = fp / (fp + tn) if (fp + tn) else 0.0
            acc = float(np.mean(pred == y_true))
            score = acc - (0.2 * fpr)
            meets_fpr = fpr <= max_fpr
            meets_acc = acc >= min_acc
            candidate = (meets_fpr and meets_acc, meets_fpr, score, float(thr), acc, float(fpr))
            if best is None or candidate > best:
                best = candidate

        assert best is not None
        _, _, _, thr, acc, fpr = best
        return thr, acc, fpr

    def fit(self, x: np.ndarray, y: np.ndarray, sequence_length: int) -> dict[str, float]:
        self.sequence_length = sequence_length
        x_scaled = self.scaler.fit_transform(x)

        if len(x_scaled) < 5:
            model = MLPClassifier(
                hidden_layer_sizes=(32,),
                random_state=self.config.random_state,
                max_iter=1,
                warm_start=True,
                early_stopping=False,
            )
            for _ in range(self.config.epochs):
                model.fit(x_scaled, y)
            self.models = [model]
            self.vector_dim = x.shape[1]
            self.decision_threshold = 0.5
            return {
                "val_accuracy": float(np.mean(model.predict(x_scaled) == y)),
                "val_loss": 0.0,
                "val_fpr": 0.0,
                "decision_threshold": self.decision_threshold,
                "mean_uncertainty": 0.0,
                "ensemble_models": float(len(self.models)),
                "epochs_trained": float(self.config.epochs),
            }

        values, counts = np.unique(y, return_counts=True)
        stratify = y if len(values) > 1 and np.min(counts) >= 2 else None

        x_train, x_val, y_train, y_val = train_test_split(
            x_scaled,
            y,
            test_size=self.config.validation_split,
            random_state=self.config.random_state,
            stratify=stratify,
        )

        best_loss = float("inf")
        patience_counter = 0
        total_epochs = 0

        for idx in range(self.config.ensemble_size):
            arch = self.config.hidden_layer_sizes[idx % len(self.config.hidden_layer_sizes)]
            model, loss, epochs_ran = self._fit_model_by_epochs(
                x_train=x_train,
                y_train=y_train,
                x_val=x_val,
                y_val=y_val,
                arch=arch,
                seed=self.config.random_state + idx,
            )
            total_epochs += epochs_ran

            if loss < best_loss:
                best_loss = loss
                patience_counter = 0
            else:
                patience_counter += 1

            self.models.append(model)
            if patience_counter >= self.config.patience:
                break

        self.vector_dim = x.shape[1]
        avg_prob = self.predict_proba_from_vectors(x_val)
        threshold, val_acc, val_fpr = self._pick_threshold(y_val, avg_prob, max_fpr=0.03)
        self.decision_threshold = threshold
        uncertainty = float(np.mean(np.std(self._ensemble_probs(x_val), axis=0)))

        return {
            "val_accuracy": val_acc,
            "val_loss": float(best_loss),
            "val_fpr": float(val_fpr),
            "decision_threshold": float(self.decision_threshold),
            "mean_uncertainty": uncertainty,
            "ensemble_models": float(len(self.models)),
            "epochs_trained": float(total_epochs),
        }

    def _ensemble_probs(self, x_vectors_scaled: np.ndarray) -> np.ndarray:
        probs = []
        for model in self.models:
            p = model.predict_proba(x_vectors_scaled)[:, 1]
            probs.append(p)
        return np.array(probs, dtype=np.float32)

    def predict_proba_from_vectors(self, x_vectors: np.ndarray) -> np.ndarray:
        selected_feature_indices = getattr(self, "selected_feature_indices", [])
        if selected_feature_indices:
            x_vectors = x_vectors[:, selected_feature_indices]
        x_scaled = self.scaler.transform(x_vectors)
        ensemble_probs = self._ensemble_probs(x_scaled)
        return np.mean(ensemble_probs, axis=0)

    def predict_risk(self, event_rows: np.ndarray) -> float:
        if len(event_rows) == 0:
            return 0.0

        windows = []
        seq = self.sequence_length
        if len(event_rows) < seq:
            pad_count = seq - len(event_rows)
            pad = np.repeat(event_rows[:1], pad_count, axis=0)
            candidate = np.vstack([pad, event_rows])
            windows.append(candidate)
        else:
            for end in range(seq, len(event_rows) + 1):
                windows.append(event_rows[end - seq : end])

        windows_arr = np.array(windows, dtype=np.float32)
        vectors = self._window_to_vector(windows_arr)
        probs = self.predict_proba_from_vectors(vectors)
        return float(np.max(probs))

    @staticmethod
    def _window_to_vector(windows: np.ndarray) -> np.ndarray:
        mean = np.mean(windows, axis=1)
        std = np.std(windows, axis=1)
        maxv = np.max(windows, axis=1)
        minv = np.min(windows, axis=1)
        return np.concatenate([mean, std, maxv, minv], axis=1).astype(np.float32)
