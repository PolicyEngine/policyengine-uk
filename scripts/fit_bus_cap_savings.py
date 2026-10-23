"""Fit the table of uncapped single bus fares to public facts.

Prints the three-band table for gov.dft.bus.uncapped_single_fares (the share
of single tickets in each band and its mean uncapped fare, at FY2024-25
prices) that best matches the facts below, and the value of each fact under
it. Fares move between years with the engine's OBR CPI index, as the
parameter's uprating does. See docs/engineering/bus-fares.md.

Run with ``uv run python scripts/fit_bus_cap_savings.py``.
"""

import numpy as np

from policyengine_uk.system import system

SINGLE_SHARE = 0.70  # gov.dft.bus.default_single_fare_share
# DfT BUS01a journeys less BUS01c concessionary journeys, England outside London.
FARE_PAYING_2023_24 = 1_780_912_900.016 - 499_730_082.115
FARE_PAYING_2024_25 = 1_850_509_887.261 - 519_107_608.594
# The benchmark yield at the December 2024 BUS0415a level, just before the
# January 2025 step: 1.554716967657 * 185.9 / 190.2282.
YIELD_DECEMBER_2024 = 1.554716967657 * 185.9 / 190.2282

# Each fact: target and tolerance, relative (a share of the target) or absolute.
FACTS = {
    # BUS05bi fare cap support, 2023-24, a full year at GBP 2 (GBP m).
    "grant_2023_24": (278.951028, 0.10, "relative"),
    # Part of the December 2024 to March 2025 BUS0415a step outside London
    # (+11.0%; neighbouring quarters moved 0.1% to 2.3%) due to the cap rising
    # from GBP 2 to GBP 3, as a share of the yield.
    "january_2025_step": (0.10, 0.01, "absolute"),
    # Funding of "over GBP 150 million" for the GBP 3 cap in 2025 (GBP m).
    "cap_3_in_2025": (150, 0.20, "relative"),
    # GBP 400 million backing the GBP 2 cap in 2027 (GBP m), read as GBP 2
    # against no cap: the GBP 3 scheme is funded only to December 2026 and the
    # GBP 2 scheme replaces it. Read as GBP 2 against a continued GBP 3 cap, the
    # fitted table gives about GBP 247m, 38% below (see UNFITTED below).
    "cap_2_in_2027": (400, 0.20, "relative"),
    # Frontier Economics and SYSTRA for DfT, Table 6: all single tickets
    # averaged GBP 2.15 before the cap; those above GBP 2 averaged GBP 2.73,
    # and GBP 0.32 / (2.73 - 2.00) puts their share near 0.44. Used for shape,
    # at face value.
    "mean_single_fare": (2.15, 0.10, "absolute"),
    "share_above_2": (0.44, 0.05, "absolute"),
    "mean_above_2": (2.73, 0.10, "absolute"),
}


# Published figures the fit reports but does not target (GBP m).
UNFITTED = {
    # BUS05bi fare cap support for 2024-25, the benchmark year: GBP 2 for 270
    # days, then GBP 3. Grant per fare-paying boarding rose 78% on 2023-24
    # while fares rose 3% to 7% and the cap rose for the last quarter, so the
    # figure may hold more than that year's forgone fares (timing or coverage
    # of payments, not checked). The 2023-24 grant and the two announced
    # figures all put a full year at GBP 2 near GBP 0.3bn, not GBP 0.6bn.
    "grant_2024_25": 515.693217,
    # The GBP 400m read the other way, as GBP 2 against a continued GBP 3 cap.
    "cap_2_against_3_in_2027": 400,
}


def price_ratios():
    cpi = system.parameters.gov.economic_assumptions.indices.obr.consumer_price_index
    base = cpi("2024-01-01")
    return {year: cpi(f"{year}-01-01") / base for year in (2023, 2025, 2027)}


def unfitted(shares, fares, ratios):
    in_force_2024_25 = sum(
        s * (f - (270 * min(f, 2) + 95 * min(f, 3)) / 365)
        for s, f in zip(shares, fares)
    )
    return {
        "grant_2024_25": SINGLE_SHARE * FARE_PAYING_2024_25 / 1e6 * in_force_2024_25,
        "cap_2_against_3_in_2027": SINGLE_SHARE
        * FARE_PAYING_2024_25
        / 1e6
        * (
            saving(shares, fares, 2, ratios[2027])
            - saving(shares, fares, 3, ratios[2027])
        ),
    }


def saving(shares, fares, cap, ratio=1.0):
    """Mean saving per single ticket from a cap: sum of share * (fare - cap)+."""
    return sum(s * np.maximum(ratio * f - cap, 0) for s, f in zip(shares, fares))


def facts(shares, fares, ratios):
    low, middle, high = shares
    above = middle + high
    return {
        "grant_2023_24": SINGLE_SHARE
        * FARE_PAYING_2023_24
        / 1e6
        * saving(shares, fares, 2, ratios[2023]),
        "january_2025_step": SINGLE_SHARE
        * (saving(shares, fares, 2) - saving(shares, fares, 3))
        / YIELD_DECEMBER_2024,
        "cap_3_in_2025": SINGLE_SHARE
        * FARE_PAYING_2024_25
        / 1e6
        * saving(shares, fares, 3, ratios[2025]),
        "cap_2_in_2027": SINGLE_SHARE
        * FARE_PAYING_2024_25
        / 1e6
        * saving(shares, fares, 2, ratios[2027]),
        "mean_single_fare": sum(s * f for s, f in zip(shares, fares)),
        "share_above_2": above,
        "mean_above_2": (middle * fares[1] + high * fares[2]) / above,
    }


def loss(values):
    total = 0
    for name, (target, tolerance, kind) in FACTS.items():
        gap = values[name] / target - 1 if kind == "relative" else values[name] - target
        total = total + (gap / tolerance) ** 2
    return total


def fit():
    """Grid search at one point of share and one penny of fare. Each band's
    mean sits at least 10% above its lower edge (GBP 2.20 and GBP 3.30), and
    the low band's fare closes the Table 6 mean of GBP 2.15."""
    ratios = price_ratios()
    middle_fare, high_fare = np.meshgrid(
        np.arange(220, 300) / 100, np.arange(330, 600) / 100, indexing="ij"
    )
    best = (np.inf, None)
    for middle in np.arange(10, 61) / 100:
        for high in np.arange(2, 41) / 100:
            low = round(1 - middle - high, 2)
            if low <= 0:
                continue
            low_fare = (2.15 - middle * middle_fare - high * high_fare) / low
            low_fare = np.round(low_fare, 2)
            valid = (low_fare > 0) & (low_fare <= 2)
            shares = (low, middle, high)
            values = facts(shares, (low_fare, middle_fare, high_fare), ratios)
            score = np.where(valid, loss(values), np.inf)
            index = np.unravel_index(np.argmin(score), score.shape)
            if score[index] < best[0]:
                fares = (low_fare[index], middle_fare[index], high_fare[index])
                best = (score[index], (shares, fares))
    return best


if __name__ == "__main__":
    score, (shares, fares) = fit()
    print(f"loss {score:.3f}")
    for band, share, fare in zip(("LOW", "MIDDLE", "HIGH"), shares, fares):
        print(f"{band:7s} share {share:.2f}  fare GBP {fare:.2f}")
    values = facts(shares, fares, price_ratios())
    for name, (target, tolerance, kind) in FACTS.items():
        print(f"{name:18s} {values[name]:9.4f}  target {target}")
    checks = unfitted(shares, fares, price_ratios())
    for name, published in UNFITTED.items():
        print(f"{name:24s} {checks[name]:9.4f}  published {published}, not fitted")
