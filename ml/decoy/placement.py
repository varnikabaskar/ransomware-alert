from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN


def strategized_decoy_placement(file_paths: list[str], file_sizes: list[int], depth_levels: list[int]) -> list[str]:
    if not file_paths:
        return []

    size_norm = np.array(file_sizes, dtype=np.float32)
    if np.max(size_norm) > 0:
        size_norm = size_norm / np.max(size_norm)

    depth = np.array(depth_levels, dtype=np.float32)
    if np.max(depth) > 0:
        depth = depth / np.max(depth)

    features = np.column_stack([size_norm, depth])
    clustering = DBSCAN(eps=0.25, min_samples=2).fit(features)
    labels = clustering.labels_

    selected = []
    for cluster_id in set(labels.tolist()):
        indices = np.where(labels == cluster_id)[0]
        if cluster_id == -1:
            # Outliers are usually high-risk directories for decoy placement.
            selected.extend(indices.tolist())
            continue
        center = np.mean(features[indices], axis=0)
        dist = np.linalg.norm(features[indices] - center, axis=1)
        selected.append(int(indices[int(np.argmin(dist))]))

    unique = sorted(set(selected))[: max(3, len(file_paths) // 10)]
    return [str(Path(file_paths[i])) for i in unique]
