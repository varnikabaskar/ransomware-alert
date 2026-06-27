from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score
from sklearn.model_selection import train_test_split

from ml.behavioral.dataset import build_sliding_windows, load_behavioral_csv
from ml.behavioral.feature_extractor import summarize_sequence_stats
from ml.common import BEHAVIORAL_MODEL_PATH, DECOY_MODEL_PATH, PROJECT_DIR
from ml.decoy.dataset import load_decoy_csv


def _can_stratify(y: np.ndarray) -> bool:
    values, counts = np.unique(y, return_counts=True)
    return len(values) > 1 and np.min(counts) >= 2


def _normalize_score(raw_prob: np.ndarray, threshold: float) -> np.ndarray:
    denom = max(1e-6, 1.0 - float(threshold))
    return np.clip((raw_prob - float(threshold)) / denom, 0.0, 1.0)


def _eval_binary(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float]:
    pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "accuracy": float(accuracy_score(y_true, pred)),
        "fpr": float(fpr),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
    }


def _pick_threshold(y_true: np.ndarray, scores: np.ndarray, max_fpr: float, min_acc: float) -> tuple[float, dict[str, float]]:
    best = None
    best_metrics: dict[str, float] | None = None
    for thr in np.linspace(0.05, 0.95, 181):
        m = _eval_binary(y_true, scores, float(thr))
        meets_fpr = m["fpr"] <= max_fpr
        meets_acc = m["accuracy"] >= min_acc
        objective = m["accuracy"] - (0.2 * m["fpr"])
        candidate = (meets_fpr and meets_acc, meets_fpr, objective, float(thr))
        if best is None or candidate > best:
            best = candidate
            best_metrics = m

    assert best is not None and best_metrics is not None
    return best[3], best_metrics


def _update_env_values(env_path: Path, updates: dict[str, str]) -> None:
    formatted = {k: str(v) for k, v in updates.items()}

    if not env_path.exists():
        content = "\n".join([f"{k}={v}" for k, v in formatted.items()]) + "\n"
        env_path.write_text(content, encoding="utf-8")
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    pending = set(formatted.keys())
    out = []
    for item in lines:
        stripped = item.strip()
        if "=" in stripped:
            key, _ = stripped.split("=", 1)
            key = key.strip()
            if key in formatted:
                out.append(f"{key}={formatted[key]}")
                pending.discard(key)
                continue
        out.append(item)

    for key in pending:
        out.append(f"{key}={formatted[key]}")

    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _build_mixture_dataset(
    beh_score: np.ndarray,
    beh_labels: np.ndarray,
    dec_score: np.ndarray,
    dec_labels: np.ndarray,
    behavioral_weight: float,
    decoy_weight: float,
    pair_count: int,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    beh_only_scores = np.clip(behavioral_weight * beh_score, 0.0, 1.0)
    dec_only_scores = np.clip(decoy_weight * dec_score, 0.0, 1.0)

    rng = np.random.default_rng(random_state)
    n_pairs = int(max(1, min(pair_count, len(beh_score) * len(dec_score))))
    bi = rng.integers(0, len(beh_score), size=n_pairs)
    di = rng.integers(0, len(dec_score), size=n_pairs)
    both_scores = np.clip((behavioral_weight * beh_score[bi]) + (decoy_weight * dec_score[di]), 0.0, 1.0)
    both_labels = np.maximum(beh_labels[bi].astype(int), dec_labels[di].astype(int))

    all_scores = np.concatenate([beh_only_scores, dec_only_scores, both_scores]).astype(np.float32)
    all_labels = np.concatenate([beh_labels.astype(int), dec_labels.astype(int), both_labels]).astype(int)
    return all_scores, all_labels, n_pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune final combined alert threshold.")
    parser.add_argument("--behavioral-csv", default=str(PROJECT_DIR / "data/behavioral/combined_without_3gram.csv"))
    parser.add_argument("--decoy-csv", default=str(PROJECT_DIR / "data/decoy/Final_Dataset_without_duplicate.csv"))
    parser.add_argument("--sequence-length", type=int, default=20)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--behavioral-weight", type=float, default=0.65)
    parser.add_argument("--decoy-weight", type=float, default=0.35)
    parser.add_argument("--pair-count", type=int, default=5000)
    parser.add_argument("--max-fpr", type=float, default=0.03)
    parser.add_argument("--min-accuracy", type=float, default=0.97)
    parser.add_argument("--search-weights", action="store_true", help="Search fusion weights over a fixed grid")
    parser.add_argument("--apply", action="store_true", help="Write tuned threshold to .env")
    args = parser.parse_args()

    if not BEHAVIORAL_MODEL_PATH.exists() or not DECOY_MODEL_PATH.exists():
        raise FileNotFoundError("Trained models are missing. Run /train first.")

    beh_model = joblib.load(BEHAVIORAL_MODEL_PATH)
    dec_model = joblib.load(DECOY_MODEL_PATH)

    xb, yb = load_behavioral_csv(args.behavioral_csv)
    wb, lb = build_sliding_windows(xb, yb, sequence_length=args.sequence_length)
    yb_strat = lb if _can_stratify(lb) else None
    wb_train, wb_test, yb_train, yb_test = train_test_split(
        wb,
        lb,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=yb_strat,
    )
    beh_test_features = summarize_sequence_stats(wb_test)
    beh_test_probs = beh_model.predict_proba_from_vectors(beh_test_features)
    beh_threshold = float(getattr(beh_model, "decision_threshold", 0.5))
    beh_score = _normalize_score(beh_test_probs, beh_threshold)

    xd, yd = load_decoy_csv(args.decoy_csv)
    yd_strat = yd if _can_stratify(yd) else None
    xd_train, xd_test, yd_train, yd_test = train_test_split(
        xd,
        yd,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=yd_strat,
    )
    dec_test_probs = dec_model.predict_proba(xd_test)[:, 1]
    dec_threshold = float(getattr(dec_model, "decision_threshold", 0.5))
    dec_score = _normalize_score(dec_test_probs, dec_threshold)

    search_space = [(args.behavioral_weight, args.decoy_weight)]
    if args.search_weights:
        search_space = []
        for bw in np.linspace(0.1, 0.9, 17):
            dw = 1.0 - float(bw)
            search_space.append((float(bw), float(dw)))

    best = None
    best_payload = None
    for behavioral_weight, decoy_weight in search_space:
        all_scores, all_labels, n_pairs = _build_mixture_dataset(
            beh_score,
            yb_test,
            dec_score,
            yd_test,
            behavioral_weight,
            decoy_weight,
            args.pair_count,
            args.random_state,
        )
        final_threshold, final_metrics = _pick_threshold(all_labels, all_scores, args.max_fpr, args.min_accuracy)

        beh_only_scores = np.clip(behavioral_weight * beh_score, 0.0, 1.0)
        dec_only_scores = np.clip(decoy_weight * dec_score, 0.0, 1.0)
        rng = np.random.default_rng(args.random_state)
        bi = rng.integers(0, len(beh_score), size=n_pairs)
        di = rng.integers(0, len(dec_score), size=n_pairs)
        both_scores = np.clip((behavioral_weight * beh_score[bi]) + (decoy_weight * dec_score[di]), 0.0, 1.0)
        both_labels = np.maximum(yb_test[bi].astype(int), yd_test[di].astype(int))

        objective = float(final_metrics["accuracy"] - (0.2 * final_metrics["fpr"]))
        candidate = (
            final_metrics["fpr"] <= args.max_fpr and final_metrics["accuracy"] >= args.min_accuracy,
            final_metrics["fpr"] <= args.max_fpr,
            objective,
            float(behavioral_weight),
        )
        payload = {
            "status": "ok",
            "inputs": {
                "behavioral_csv": str(Path(args.behavioral_csv)),
                "decoy_csv": str(Path(args.decoy_csv)),
                "sequence_length": args.sequence_length,
                "test_size": args.test_size,
                "random_state": args.random_state,
                "weights": {"behavioral": behavioral_weight, "decoy": decoy_weight},
                "pair_count": n_pairs,
                "search_weights": bool(args.search_weights),
            },
            "model_thresholds": {
                "behavioral_decision_threshold": beh_threshold,
                "decoy_decision_threshold": dec_threshold,
            },
            "final_alert_threshold": float(final_threshold),
            "final_metrics": final_metrics,
            "scenario_breakdown": {
                "behavioral_only": _eval_binary(yb_test.astype(int), beh_only_scores, final_threshold),
                "decoy_only": _eval_binary(yd_test.astype(int), dec_only_scores, final_threshold),
                "both_present": _eval_binary(both_labels, both_scores, final_threshold),
            },
        }
        if best is None or candidate > best:
            best = candidate
            best_payload = payload

    assert best_payload is not None
    payload = best_payload

    if args.apply:
        env_path = PROJECT_DIR / ".env"
        weights = payload["inputs"]["weights"]
        _update_env_values(
            env_path,
            {
                "R_GUARD_ALERT_THRESHOLD": f"{float(payload['final_alert_threshold']):.4f}",
                "R_GUARD_BEHAVIORAL_WEIGHT": f"{float(weights['behavioral']):.4f}",
                "R_GUARD_DECOY_WEIGHT": f"{float(weights['decoy']):.4f}",
            },
        )
        payload["applied_to_env"] = str(env_path)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
