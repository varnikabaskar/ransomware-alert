from __future__ import annotations

import numpy as np
from sklearn.feature_selection import mutual_info_classif


class IncrementalMutualFeatureSelector:
    """Incremental MI selector with redundancy penalty.

    This approximates a lightweight mRMR strategy that prioritizes features
    with strong target relevance while reducing redundant picks.
    """

    def __init__(self, max_features: int = 18, redundancy_weight: float = 0.25, random_state: int = 42) -> None:
        self.max_features = max(1, int(max_features))
        self.redundancy_weight = float(np.clip(redundancy_weight, 0.0, 1.0))
        self.random_state = int(random_state)
        self.selected_indices: np.ndarray = np.array([], dtype=np.int32)
        self.mi_scores: np.ndarray = np.array([], dtype=np.float32)

    def fit(self, x: np.ndarray, y: np.ndarray) -> "IncrementalMutualFeatureSelector":
        n_features = x.shape[1]
        k = min(self.max_features, n_features)

        mi = mutual_info_classif(x, y, discrete_features=False, random_state=self.random_state)
        mi = np.nan_to_num(mi, nan=0.0, posinf=0.0, neginf=0.0)

        selected: list[int] = []
        remaining = set(range(n_features))

        first = int(np.argmax(mi))
        selected.append(first)
        remaining.discard(first)

        while len(selected) < k and remaining:
            best_idx = None
            best_score = -1e9

            for idx in remaining:
                relevance = float(mi[idx])
                redundancy = 0.0
                if selected:
                    corr = []
                    for s in selected:
                        c = np.corrcoef(x[:, idx], x[:, s])[0, 1]
                        if np.isnan(c):
                            c = 0.0
                        corr.append(abs(float(c)))
                    redundancy = float(np.mean(corr)) if corr else 0.0

                score = relevance - (self.redundancy_weight * redundancy)
                if score > best_score:
                    best_score = score
                    best_idx = idx

            if best_idx is None:
                break
            selected.append(int(best_idx))
            remaining.discard(int(best_idx))

        self.selected_indices = np.array(sorted(selected), dtype=np.int32)
        self.mi_scores = mi.astype(np.float32)
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        if self.selected_indices.size == 0:
            return x
        return x[:, self.selected_indices]

    def fit_transform(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        self.fit(x, y)
        return self.transform(x)
