from __future__ import annotations

import multiprocessing
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from app.config import get_settings


def _chunk_data(data: np.ndarray, num_chunks: int) -> list[np.ndarray]:
    if len(data) == 0:
        return []
    chunk_size = max(1, len(data) // num_chunks + (1 if len(data) % num_chunks else 0))
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def _mapper_assign(chunk: np.ndarray, centroids: np.ndarray) -> list[tuple[int, np.ndarray]]:
    assignments: list[tuple[int, np.ndarray]] = []
    for point in chunk:
        distances = [np.linalg.norm(point - c) for c in centroids]
        nearest = int(np.argmin(distances))
        assignments.append((nearest, point))
    return assignments


def _reducer_update(
    assignments: list[tuple[int, np.ndarray]], num_clusters: int, old_centroids: np.ndarray
) -> np.ndarray:
    cluster_points: dict[int, list[np.ndarray]] = {i: [] for i in range(num_clusters)}
    for cluster_idx, point in assignments:
        cluster_points[cluster_idx].append(point)

    new_centroids = old_centroids.copy()
    for i in range(num_clusters):
        if cluster_points[i]:
            new_centroids[i] = np.mean(cluster_points[i], axis=0)
    return new_centroids


def kmeans_cluster(
    features: np.ndarray,
    num_clusters: int | None = None,
    max_iter: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """K-Means using MapReduce-style map/reduce steps (HW2 methodology)."""
    settings = get_settings()
    k = num_clusters or settings.kmeans_clusters
    iterations = max_iter or settings.kmeans_max_iter
    workers = settings.mapreduce_workers

    if len(features) == 0:
        return np.array([]), np.array([])

    k = min(k, len(features))
    rng = np.random.default_rng(42)
    indices = rng.choice(len(features), size=k, replace=False)
    centroids = features[indices].astype(float)

    labels = np.zeros(len(features), dtype=int)

    for _ in range(iterations):
        chunks = _chunk_data(features, workers)
        all_assignments: list[tuple[int, np.ndarray]] = []

        if settings.use_multiprocessing and len(chunks) > 1:
            with multiprocessing.Pool(processes=min(workers, len(chunks))) as pool:
                mapped = pool.starmap(_mapper_assign, [(c, centroids) for c in chunks])
                for partial in mapped:
                    all_assignments.extend(partial)
        else:
            with ThreadPoolExecutor(max_workers=min(workers, len(chunks))) as executor:
                mapped = list(executor.map(lambda c: _mapper_assign(c, centroids), chunks))
                for partial in mapped:
                    all_assignments.extend(partial)

        new_centroids = _reducer_update(all_assignments, k, centroids)
        labels = np.array([idx for idx, _ in all_assignments], dtype=int)

        if np.allclose(centroids, new_centroids, atol=1e-4):
            centroids = new_centroids
            break
        centroids = new_centroids

    return labels, centroids


SEGMENT_LABELS = ["高價值忠誠客", "潛力成長客", "流失風險客"]


def label_clusters(centroids: np.ndarray) -> list[str]:
    if len(centroids) == 0:
        return []

    # Lower recency + higher monetary/frequency => higher value
    scores = []
    for c in centroids:
        recency, frequency, monetary = c
        score = (1.0 / (recency + 1.0)) + frequency + monetary / 1000.0
        scores.append(score)

    ranked = np.argsort(scores)[::-1]
    labels = [""] * len(centroids)
    for rank, cluster_idx in enumerate(ranked):
        if rank < len(SEGMENT_LABELS):
            labels[cluster_idx] = SEGMENT_LABELS[rank]
        else:
            labels[cluster_idx] = f"客群 {cluster_idx}"
    return labels
