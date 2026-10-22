"""Protein / cost / CO2 calculator for yeast + plant hybrid meat variants.

All ingredient numbers are ROUGH ESTIMATES for prototyping. Replace them with
your supplier labels and a proper LCA database before drawing conclusions.
"""
from typing import Dict

# name: (protein g per 100 g, cost USD per kg, kg CO2e per kg)
INGREDIENTS: Dict[str, tuple] = {
    "textured_pea":    (50.0, 5.0, 1.2),
    "yeast_spent":     (45.0, 1.0, 0.3),   # debittered spent brewer's yeast (by-product)
    "methylcellulose": (0.0, 15.0, 2.0),
    "fat_blend":       (0.0, 3.5, 2.0),    # coconut + sunflower oil
    "beet_powder":     (10.0, 10.0, 0.8),
    "flavour_mix":     (30.0, 9.0, 1.5),   # yeast extract, miso, spices
    "water":           (0.0, 0.0, 0.0),
}
BEEF = {"name": "beef mince (reference)", "protein": 20.0, "cost": 12.0, "co2": 27.0}

# Variants: grams per 100 g of mix. Water fills the balance.
def make_variant(yeast: float, fat: float = 9.0, binder: float = 1.5) -> Dict[str, float]:
    r = {"textured_pea": 42.0 - yeast * 0.5, "yeast_spent": yeast,
         "methylcellulose": binder, "fat_blend": fat, "beet_powder": 2.0,
         "flavour_mix": 4.0}
    r["water"] = 100.0 - sum(r.values())
    if r["water"] < 0:
        raise ValueError("recipe exceeds 100 g")
    return r

VARIANTS = {f"yeast_{y}%": make_variant(y) for y in (0, 10, 15, 20)}


def evaluate(recipe: Dict[str, float]) -> Dict[str, float]:
    """Per 100 g: protein (g), cost (USD/kg), CO2e (kg/kg). Recipe is grams per 100 g."""
    total = sum(recipe.values())
    protein = sum(g * INGREDIENTS[n][0] / 100 for n, g in recipe.items())
    cost = sum(g * INGREDIENTS[n][1] for n, g in recipe.items()) / total
    co2 = sum(g * INGREDIENTS[n][2] for n, g in recipe.items()) / total
    return {"protein_g_per_100g": protein, "cost_usd_per_kg": cost, "co2e_kg_per_kg": co2}


def main():
    print(f"{'variant':<12}{'protein/100g':>14}{'$/kg':>8}{'kgCO2e/kg':>11}{'CO2 vs beef':>13}")
    for name, rec in VARIANTS.items():
        m = evaluate(rec)
        print(f"{name:<12}{m['protein_g_per_100g']:>14.1f}{m['cost_usd_per_kg']:>8.2f}"
              f"{m['co2e_kg_per_kg']:>11.2f}{(1 - m['co2e_kg_per_kg'] / BEEF['co2']) * 100:>12.0f}%")
    print(f"{'beef':<12}{BEEF['protein']:>14.1f}{BEEF['cost']:>8.2f}{BEEF['co2']:>11.2f}")


if __name__ == "__main__":
    main()
