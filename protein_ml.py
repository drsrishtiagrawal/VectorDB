"""ML-guided formulation: learn taste from panel scores, then search for the best recipe.

Model: ridge-regularised quadratic regression (pure Python) mapping
(yeast %, fat %, binder %) -> predicted taste score (1-5).
Optimiser: random search maximising predicted taste while penalising CO2 and cost,
subject to a minimum protein level. Each real tasting round adds data -> retrain.

NOTE: panel_scores.csv ships with ILLUSTRATIVE placeholder data. Replace it with
your own tasting results.
"""
import csv
import random
import sys
from itertools import combinations_with_replacement

from protein_calc import BEEF, evaluate, make_variant

FEATURES = ["yeast_pct", "fat_pct", "binder_pct"]


def expand(x):
    """Quadratic feature expansion: 1, x_i, x_i*x_j."""
    out = [1.0] + list(x)
    out += [a * b for a, b in combinations_with_replacement(x, 2)]
    return out


def solve(A, b):
    """Gaussian elimination with partial pivoting."""
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


class TasteModel:
    def __init__(self, ridge=0.5):
        self.ridge = ridge
        self.mean = self.scale = self.w = None

    def _norm(self, x):
        return [(v - m) / s for v, m, s in zip(x, self.mean, self.scale)]

    def fit(self, X, y):
        cols = list(zip(*X))
        self.mean = [sum(c) / len(c) for c in cols]
        self.scale = [(sum((v - m) ** 2 for v in c) / len(c)) ** 0.5 or 1.0
                      for c, m in zip(cols, self.mean)]
        F = [expand(self._norm(x)) for x in X]
        d = len(F[0])
        A = [[sum(f[i] * f[j] for f in F) + (self.ridge if i and i == j else 0.0)
              for j in range(d)] for i in range(d)]
        b = [sum(f[i] * t for f, t in zip(F, y)) for i in range(d)]
        self.w = solve(A, b)
        return self

    def predict(self, x):
        return sum(w * f for w, f in zip(self.w, expand(self._norm(x))))


def load(path):
    X, y = [], []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            X.append([float(row[f]) for f in FEATURES])
            y.append(float(row["taste_score"]))
    return X, y


def loo_rmse(X, y):
    """Leave-one-out error: how far off the model is on unseen recipes."""
    err = 0.0
    for i in range(len(X)):
        m = TasteModel().fit(X[:i] + X[i + 1:], y[:i] + y[i + 1:])
        err += (m.predict(X[i]) - y[i]) ** 2
    return (err / len(X)) ** 0.5


def optimise(model, min_protein=18.0, w_co2=0.05, w_cost=0.03, iters=20000, seed=0):
    rng = random.Random(seed)
    best = None
    for _ in range(iters):
        y_, f_, b_ = rng.uniform(0, 20), rng.uniform(5, 12), rng.uniform(0.5, 2.5)
        try:
            m = evaluate(make_variant(y_, f_, b_))
        except ValueError:
            continue
        if m["protein_g_per_100g"] < min_protein:
            continue
        taste = max(1.0, min(5.0, model.predict([y_, f_, b_])))
        score = taste - w_co2 * m["co2e_kg_per_kg"] * 10 - w_cost * m["cost_usd_per_kg"]
        if best is None or score > best[0]:
            best = (score, taste, (y_, f_, b_), m)
    return best


def main(path="panel_scores.csv"):
    X, y = load(path)
    print(f"Loaded {len(X)} tasting results; leave-one-out RMSE = {loo_rmse(X, y):.2f} (score points)")
    model = TasteModel().fit(X, y)
    best = optimise(model)
    if not best:
        sys.exit("No recipe satisfies the constraints.")
    _, taste, (yp, fp, bp), m = best
    print("\nSuggested next recipe to cook and taste:")
    print(f"  yeast {yp:.1f}% | fat {fp:.1f}% | binder {bp:.2f}%")
    print(f"  predicted taste {taste:.2f}/5 | protein {m['protein_g_per_100g']:.1f} g/100g | "
          f"${m['cost_usd_per_kg']:.2f}/kg | {m['co2e_kg_per_kg']:.2f} kgCO2e/kg "
          f"({(1 - m['co2e_kg_per_kg'] / BEEF['co2']) * 100:.0f}% below beef)")
    print("\nLoop: cook it, add the panel score as a new row in panel_scores.csv, rerun.")


if __name__ == "__main__":
    main(*sys.argv[1:2])
