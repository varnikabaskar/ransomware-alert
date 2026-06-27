from __future__ import annotations

import numpy as np


class BiGradMinimalGAN:
    """Compact GAN-inspired synthesizer for tabular behavioral vectors.

    This is a production-safe approximation that models class-conditional
    distributions and uses a bi-gradual noise schedule to refine synthetic
    samples without destabilizing training.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = int(random_state)
        self._rng = np.random.default_rng(self.random_state)
        self._class_stats: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    def fit(self, x: np.ndarray, y: np.ndarray) -> "BiGradMinimalGAN":
        self._class_stats.clear()
        classes = np.unique(y)
        for c in classes:
            subset = x[y == c]
            if len(subset) == 0:
                continue
            mu = np.mean(subset, axis=0)
            sigma = np.std(subset, axis=0)
            sigma = np.maximum(sigma, 1e-4)
            self._class_stats[int(c)] = (mu.astype(np.float32), sigma.astype(np.float32))
        return self

    def synthesize(self, target_class: int, n_samples: int, realism_cycles: int = 3) -> np.ndarray:
        if target_class not in self._class_stats or n_samples <= 0:
            return np.empty((0, 0), dtype=np.float32)

        mu, sigma = self._class_stats[target_class]
        base = self._rng.normal(loc=mu, scale=sigma, size=(n_samples, len(mu))).astype(np.float32)

        # Bi-gradual schedule: coarse perturbation followed by fine refinement.
        for cycle in range(max(1, int(realism_cycles))):
            coarse = max(0.04, 0.20 / (cycle + 1.0))
            fine = max(0.005, 0.05 / (cycle + 1.0))
            base = (0.80 * base) + (0.20 * self._rng.normal(loc=mu, scale=(sigma * coarse), size=base.shape))
            base = base + self._rng.normal(loc=0.0, scale=(sigma * fine), size=base.shape)

        return np.clip(base, 0.0, 1.0).astype(np.float32)

    def augment(self, x: np.ndarray, y: np.ndarray, ratio: float = 0.25) -> tuple[np.ndarray, np.ndarray]:
        if len(x) == 0:
            return x, y

        ratio = float(max(0.0, ratio))
        if ratio <= 0.0:
            return x, y

        classes, counts = np.unique(y, return_counts=True)
        max_count = int(np.max(counts))

        synth_x = []
        synth_y = []
        for c, count in zip(classes, counts):
            target = int(max(max_count, int(count + (len(x) * ratio / max(1, len(classes))))))
            need = max(0, target - int(count))
            if need == 0:
                continue
            samples = self.synthesize(int(c), need)
            if samples.size == 0:
                continue
            synth_x.append(samples)
            synth_y.append(np.full((need,), int(c), dtype=np.int32))

        if not synth_x:
            return x, y

        x_aug = np.vstack([x] + synth_x).astype(np.float32)
        y_aug = np.concatenate([y] + synth_y).astype(np.int32)
        return x_aug, y_aug
