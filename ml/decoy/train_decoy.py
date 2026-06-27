import joblib
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from ml.common import DECOY_MODEL_PATH
from ml.decoy.dataset import load_decoy_csv
from ml.decoy.random_forest_trap import DecoyRFModel


def _can_stratify(y):
    classes = set(y.tolist())
    if len(classes) < 2:
        return False
    min_count = min((y == c).sum() for c in classes)
    return int(min_count) >= 2


def _pick_threshold(
    y_true: np.ndarray,
    probs: np.ndarray,
    max_fpr: float = 0.03,
    min_acc: float = 0.97,
) -> tuple[float, float, float]:
    best = None
    for thr in np.linspace(0.05, 0.95, 181):
        pred = (probs >= thr).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
        fpr = fp / (fp + tn) if (fp + tn) else 0.0
        acc = accuracy_score(y_true, pred)
        score = acc - (0.2 * fpr)
        meets_fpr = fpr <= max_fpr
        meets_acc = acc >= min_acc
        candidate = (meets_fpr and meets_acc, meets_fpr, score, float(thr), float(acc), float(fpr))
        if best is None or candidate > best:
            best = candidate

    assert best is not None
    _, _, _, thr, acc, fpr = best
    return thr, acc, fpr


def train_decoy_pipeline(
    csv_path: str,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, float | str]:
    x, y = load_decoy_csv(csv_path)
    stratify_labels = y if _can_stratify(y) else None
    x_train_val, x_test, y_train_val, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_labels,
    )

    stratify_train = y_train_val if _can_stratify(y_train_val) else None
    x_train, x_val, y_train, y_val = train_test_split(
        x_train_val,
        y_train_val,
        test_size=0.2,
        random_state=random_state,
        stratify=stratify_train,
    )

    model = DecoyRFModel()
    model.fit(x_train, y_train)

    val_probs = model.predict_proba(x_val)[:, 1]
    threshold, val_acc, val_fpr = _pick_threshold(y_val, val_probs, max_fpr=0.03)
    model.set_decision_threshold(threshold)

    probs = model.predict_proba(x_test)[:, 1]
    pred = (probs >= model.decision_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
    test_fpr = fp / (fp + tn) if (fp + tn) else 0.0
    train_pred = (model.predict_proba(x_train)[:, 1] >= model.decision_threshold).astype(int)
    train_acc = accuracy_score(y_train, train_pred)
    test_acc = accuracy_score(y_test, pred)

    joblib.dump(model, DECOY_MODEL_PATH)

    return {
        "status": "trained",
        "model_path": str(DECOY_MODEL_PATH),
        "decision_threshold": float(model.decision_threshold),
        "val_accuracy": float(val_acc),
        "val_fpr": float(val_fpr),
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
        "test_fpr": float(test_fpr),
        "overfit_gap": float(max(0.0, train_acc - test_acc)),
        "test_f1": float(f1_score(y_test, pred)),
        "test_auc": float(roc_auc_score(y_test, probs)),
    }
