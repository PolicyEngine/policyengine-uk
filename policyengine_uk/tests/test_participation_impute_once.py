"""Non-workers' wages are imputed once per participation step (#1836, item 4).

`apply_participation_responses` used to call `impute_wages_for_nonworkers` four
times: once on the baseline inside `calculate_gain_to_work`, and three times on
the reform simulation (reform gain-to-work, earnings quintiles, entry step).
The three reform calls read the same inputs, so it now imputes once on the
reform simulation and passes the array on. These tests pin the call count and
show the outputs do not change.
"""

import numpy as np
import pandas as pd

from policyengine_uk import Simulation
from policyengine_uk.dynamics import participation as p

YEAR = 2025
# With this seed one non-worker enters work, so the entry step, which writes the
# imputed wage into employment_income, is exercised too.
SEED = 92


def situation():
    """Three couples, one earner and one non-earner each, of mixed sex and age."""
    people, benunits, households = {}, {}, {}
    couples = [
        (("MALE", 34, 28_000), ("FEMALE", 31, 0)),
        (("FEMALE", 45, 52_000), ("MALE", 47, 0)),
        (("MALE", 58, 19_000), ("FEMALE", 26, 0)),
    ]
    for c, couple in enumerate(couples):
        members = []
        for a, (gender, age, pay) in enumerate(couple):
            name = f"adult_{c}_{a}"
            people[name] = {
                "age": {str(YEAR): age},
                "gender": {str(YEAR): gender},
                "employment_income": {str(YEAR): pay},
                "hours_worked": {str(YEAR): 1_800 if pay else 0},
            }
            members.append(name)
        benunits[f"benunit_{c}"] = {"members": members}
        households[f"household_{c}"] = {"members": members}
    return {"people": people, "benunits": benunits, "households": households}


def build(monkeypatch):
    # The exclusion helper calls `.values` on its result, which a plain
    # Simulation does not return. Exclude nobody, as the other participation
    # tests do, so the real gain-to-work, quintile and draw code all run.
    from policyengine_uk.dynamics import labour_supply

    n = len(situation()["people"])
    monkeypatch.setattr(
        labour_supply,
        "calculate_excluded_from_labour_supply_responses",
        lambda *args: np.zeros(n, dtype=bool),
    )
    return Simulation(
        situation=situation(),
        reform={"gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.05}},
    )


def count_imputations(monkeypatch):
    """Wrap the real imputation so each call is recorded with its source."""
    calls = []
    real = p.impute_wages_for_nonworkers

    def counted(sim, *args, **kwargs):
        result = real(sim, *args, **kwargs)
        calls.append((sim, np.asarray(result).copy()))
        return result

    monkeypatch.setattr(p, "impute_wages_for_nonworkers", counted)
    return calls


def frame(result):
    return pd.DataFrame(result).reset_index(drop=True).astype(float)


def test_participation_step_imputes_twice_not_four_times(monkeypatch):
    sim = build(monkeypatch)
    calls = count_imputations(monkeypatch)
    p.apply_participation_responses(sim, YEAR, random_seed=SEED)
    assert len(calls) == 2
    sources = [source for source, _ in calls]
    assert sources.count(sim) == 1
    assert sources.count(sim.baseline) == 1


def test_reused_imputation_gives_identical_outputs(monkeypatch):
    """Forcing each helper to impute for itself, as before, changes nothing."""
    sim = build(monkeypatch)
    calls = count_imputations(monkeypatch)
    reused = p.apply_participation_responses(sim, YEAR, random_seed=SEED)
    reused_income = np.asarray(sim.calculate("employment_income", YEAR)).copy()
    reused_hours = np.asarray(sim.calculate("hours_worked", YEAR)).copy()
    shared = [wages for source, wages in calls if source is sim]

    # Previous behaviour: the reform gain-to-work and the earnings quintiles
    # each recompute the imputation instead of receiving it.
    real_gain = p.calculate_gain_to_work
    real_quintile = p.calculate_earnings_quintile

    def gain(*args, imputed_wages=None, **kwargs):
        return real_gain(*args, **kwargs)

    def quintile(sim, year, hours, seed, imputed_wages=None):
        return real_quintile(sim, year, hours, seed)

    monkeypatch.setattr(p, "calculate_gain_to_work", gain)
    monkeypatch.setattr(p, "calculate_earnings_quintile", quintile)
    sim = build(monkeypatch)
    calls.clear()
    legacy = p.apply_participation_responses(sim, YEAR, random_seed=SEED)

    # Every reform-side imputation the old path makes equals the shared one.
    recomputed = [wages for source, wages in calls if source is sim]
    assert len(recomputed) == 3
    for wages in recomputed:
        np.testing.assert_array_equal(wages, shared[0])
    assert (shared[0] > 0).any()

    assert reused["participation_response"].sum() == 1
    pd.testing.assert_frame_equal(frame(reused), frame(legacy))
    np.testing.assert_array_equal(
        np.asarray(sim.calculate("employment_income", YEAR)), reused_income
    )
    np.testing.assert_array_equal(
        np.asarray(sim.calculate("hours_worked", YEAR)), reused_hours
    )


def test_helpers_still_impute_when_no_array_is_passed(monkeypatch):
    sim = build(monkeypatch)
    calls = count_imputations(monkeypatch)
    computed = p.calculate_earnings_quintile(sim, YEAR)
    passed = p.calculate_earnings_quintile(
        sim, YEAR, imputed_wages=p.impute_wages_for_nonworkers(sim, YEAR)
    )
    np.testing.assert_array_equal(computed, passed)
    gain_computed = p.calculate_gain_to_work(sim, YEAR, count_adults=2)
    gain_passed = p.calculate_gain_to_work(
        sim, YEAR, count_adults=2, imputed_wages=calls[-1][1]
    )
    pd.testing.assert_frame_equal(gain_computed, gain_passed)
    # One explicit call plus one inside each helper that was given nothing.
    assert len(calls) == 3
