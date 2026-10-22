"""Minimal in-memory vector database prototype (pure Python, no dependencies)."""
import math
from typing import Any, Dict, List, Optional, Tuple


class VectorDB:
    def __init__(self, dim: int, metric: str = "cosine"):
        if metric not in ("cosine", "euclidean", "dot"):
            raise ValueError("metric must be cosine, euclidean or dot")
        self.dim = dim
        self.metric = metric
        self._vectors: Dict[str, List[float]] = {}
        self._meta: Dict[str, Dict[str, Any]] = {}

    def insert(self, id: str, vector: List[float], metadata: Optional[dict] = None) -> None:
        if len(vector) != self.dim:
            raise ValueError(f"expected dim {self.dim}, got {len(vector)}")
        self._vectors[id] = [float(x) for x in vector]
        self._meta[id] = dict(metadata or {})

    def delete(self, id: str) -> bool:
        self._meta.pop(id, None)
        return self._vectors.pop(id, None) is not None

    def get(self, id: str) -> Tuple[List[float], dict]:
        return self._vectors[id], self._meta[id]

    def __len__(self) -> int:
        return len(self._vectors)

    def _score(self, a: List[float], b: List[float]) -> float:
        """Higher is always better."""
        if self.metric == "dot":
            return sum(x * y for x, y in zip(a, b))
        if self.metric == "euclidean":
            return -math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb) if na and nb else 0.0

    def search(self, query: List[float], k: int = 5, where: Optional[dict] = None):
        """Brute-force top-k. `where` filters on exact metadata matches."""
        if len(query) != self.dim:
            raise ValueError(f"expected dim {self.dim}, got {len(query)}")
        results = []
        for id, vec in self._vectors.items():
            if where and any(self._meta[id].get(key) != v for key, v in where.items()):
                continue
            results.append((id, self._score(query, vec), self._meta[id]))
        results.sort(key=lambda r: r[1], reverse=True)
        return results[:k]
