"""VAT on private school fees is charged once, at the statutory or reform rate.

VATA 1994 Sch 9 Group 6 exempted education supplied by an eligible body,
which included registered independent schools. Finance Act 2025 s.47
inserts Sch 9 Part 3, which takes private school education, vocational
training and closely related board and lodging out of the exemption, for
supplies on or after 1 January 2025 (s.49). The fees then bear the standard
rate. gov.contrib.labour.private_school_vat is a contributed reform rate.

Invariants, for any household with up to three pupils, any year from 2024
to 2030, any mean fee, share of fees bearing VAT, standard rate and reform
rate, with the exemption at current law, restored or removed:

- differential: private_school_vat equals pupils x fee x share x the
  higher of the statutory rate (0 while the fees are exempt, the standard
  rate otherwise) and the reform rate, computed here from the statute and
  not from the model's formula;
- once: a reform rate at or below the statutory rate leaves
  private_school_vat unchanged, so the fees are never taxed twice;
- monotone: private_school_vat never falls when the reform rate or the
  standard rate rises;
- receipt partition: school-specific rate and exemption reforms leave the
  residual vat head unchanged, and private_school_vat is independent of
  recorded consumption. General VAT nets out the baseline school tax base
  before the school head is counted (test_private_school_vat_receipts.py);
- level and change: private_school_vat_change equals private_school_vat
  minus baseline_private_school_vat; baseline_private_school_vat equals
  private_school_vat under baseline policy with this simulation's mean fee
  and share of fees bearing VAT; so a reform that changes only those
  assumptions changes nothing, and the change is zero at current law.

A grid test checks the differential exhaustively over years either side of
the commencement, every setting of the exemption, reform rates below, at
and above the standard rate, and two standard rates.

Every household in an example is built in one simulation per parameter
set, so the comparisons hold attendance fixed.
"""

import numpy as np
import itertools

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

ALWAYS = "2000-01-01.2100-12-31"
CONTRIB = "gov.contrib.labour.private_school_vat"
EXEMPT = "gov.hmrc.vat.private_school_fees_exempt"
STANDARD = "gov.hmrc.vat.standard_rate"
FEES = "gov.simulation.private_school_vat.private_school_fees"
BASIS = "gov.simulation.private_school_vat.private_school_vat_basis"
# Model values are float32.
RTOL = 1e-6

household = st.fixed_dictionaries(
    {
        "pupils": st.integers(0, 3),
        "other_children": st.integers(0, 2),
        "consumption": st.one_of(st.just(0.0), st.floats(1_000, 100_000)),
        "education_share": st.floats(0, 0.5),
    }
)
parameter_set = st.fixed_dictionaries(
    {
        "year": st.integers(2024, 2030),
        "fees": st.floats(1_000, 50_000),
        "basis": st.floats(0, 1),
        "standard_rate": st.one_of(st.none(), st.sampled_from([0.15, 0.2, 0.25])),
        "exempt": st.one_of(st.none(), st.booleans()),
        "contrib": st.one_of(st.just(0.0), st.floats(0, 0.4)),
    }
)


def situation(households: list, year: int) -> dict:
    people, benunits, hhs = {}, {}, {}
    for i, h in enumerate(households):
        members = [f"adult_{i}"]
        people[f"adult_{i}"] = {"age": {year: 45}}
        for kind, count in (("pupil", h["pupils"]), ("child", h["other_children"])):
            for j in range(count):
                name = f"{kind}_{i}_{j}"
                people[name] = {
                    "age": {year: 6 + j},
                    "attends_private_school": {year: kind == "pupil"},
                }
                members.append(name)
        benunits[f"benunit_{i}"] = {"members": members}
        education = h["consumption"] * h["education_share"]
        hhs[f"household_{i}"] = {
            "members": members,
            "education_consumption": {year: education},
            "food_and_non_alcoholic_beverages_consumption": {
                year: h["consumption"] - education
            },
        }
    return {"people": people, "benunits": benunits, "households": hhs}


def reform_for(p: dict) -> dict:
    reform = {
        FEES: {ALWAYS: p["fees"]},
        BASIS: {ALWAYS: p["basis"]},
        CONTRIB: {ALWAYS: p["contrib"]},
    }
    if p["standard_rate"] is not None:
        reform[STANDARD] = {ALWAYS: p["standard_rate"]}
    if p["exempt"] is not None:
        reform[EXEMPT] = {ALWAYS: p["exempt"]}
    return reform


def statutory_rate(p: dict) -> float:
    """The statute's rate on the fees, independently of the model's formula."""
    year = p["year"]
    exempt = p["exempt"]
    if exempt is None:
        # Exempt until the s.49 commencement on 1 January 2025.
        exempt = year < 2025
    if exempt:
        return 0.0
    if p["standard_rate"] is not None:
        return p["standard_rate"]
    # VATA 1994 s.2(1): 20 per cent since 4 January 2011.
    return 0.2


def calc(households, p, variable, **overrides):
    sim = Simulation(
        situation=situation(households, p["year"]),
        reform=reform_for({**p, **overrides}),
    )
    return np.asarray(sim.calculate(variable, p["year"]), dtype=float)


def assert_close(actual, expected, message=""):
    np.testing.assert_allclose(actual, expected, rtol=RTOL, atol=1e-2, err_msg=message)


SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(households=st.lists(household, min_size=1, max_size=3), p=parameter_set)
def test_private_school_vat_matches_the_statute(households, p):
    pupils = np.array([h["pupils"] for h in households], dtype=float)
    rate = max(statutory_rate(p), p["contrib"])
    expected = pupils * p["fees"] * p["basis"] * rate
    assert_close(calc(households, p, "private_school_vat"), expected)


@SETTINGS
@given(
    households=st.lists(household, min_size=1, max_size=3),
    p=parameter_set,
    fraction=st.floats(0, 1),
)
def test_a_reform_rate_at_or_below_the_statute_never_taxes_twice(
    households, p, fraction
):
    without_reform = calc(households, p, "private_school_vat", contrib=0.0)
    at_or_below = calc(
        households, p, "private_school_vat", contrib=fraction * statutory_rate(p)
    )
    assert_close(at_or_below, without_reform)


@SETTINGS
@given(
    households=st.lists(household, min_size=1, max_size=3),
    p=parameter_set,
    rise=st.floats(0, 0.2),
)
def test_private_school_vat_never_falls_as_a_rate_rises(households, p, rise):
    before = calc(households, p, "private_school_vat")
    higher_contrib = calc(
        households, p, "private_school_vat", contrib=p["contrib"] + rise
    )
    standard = p["standard_rate"] or statutory_rate({**p, "exempt": False})
    higher_standard = calc(
        households, p, "private_school_vat", standard_rate=standard + rise
    )
    tolerance = RTOL * np.abs(before) + 1e-2
    assert (higher_contrib >= before - tolerance).all()
    assert (higher_standard >= before - tolerance).all()


@SETTINGS
@given(households=st.lists(household, min_size=1, max_size=3), p=parameter_set)
def test_school_specific_policy_leaves_residual_vat_unchanged(households, p):
    vat = calc(households, p, "vat")
    for overrides in (
        {"exempt": True, "contrib": 0.0},
        {"exempt": False, "contrib": 0.35},
    ):
        assert_close(calc(households, p, "vat", **overrides), vat, str(overrides))
    no_consumption = [
        {**h, "consumption": 0.0, "education_share": 0.0} for h in households
    ]
    assert_close(
        calc(no_consumption, p, "private_school_vat"),
        calc(households, p, "private_school_vat"),
    )


@SETTINGS
@given(households=st.lists(household, min_size=1, max_size=3), p=parameter_set)
def test_level_and_change(households, p):
    sim = Simulation(situation=situation(households, p["year"]), reform=reform_for(p))
    level, baseline, change = (
        np.asarray(sim.calculate(v, p["year"]), dtype=float)
        for v in (
            "private_school_vat",
            "baseline_private_school_vat",
            "private_school_vat_change",
        )
    )
    assert_close(change, level - baseline)
    # Baseline policy with this simulation's assumptions.
    assumptions_only = Simulation(
        situation=situation(households, p["year"]),
        reform={FEES: {ALWAYS: p["fees"]}, BASIS: {ALWAYS: p["basis"]}},
    )
    assert_close(
        baseline,
        np.asarray(
            assumptions_only.calculate("private_school_vat", p["year"]), dtype=float
        ),
    )
    for current_policy in (
        assumptions_only,
        Simulation(situation=situation(households, p["year"])),
    ):
        np.testing.assert_array_equal(
            current_policy.calculate("private_school_vat_change", p["year"]), 0
        )


GRID_HOUSEHOLDS = [
    {"pupils": n, "other_children": 1, "consumption": 20_000.0, "education_share": 0.2}
    for n in (0, 1, 3)
]
GRID = list(
    itertools.product(
        (2024, 2025),
        (None, True, False),
        (0.0, 0.1, 0.2, 0.3),
        (None, 0.25),
    )
)


@pytest.mark.parametrize("year, exempt, contrib, standard_rate", GRID)
def test_private_school_vat_grid(year, exempt, contrib, standard_rate):
    p = {
        "year": year,
        "fees": 12_000.0,
        "basis": 0.75,
        "standard_rate": standard_rate,
        "exempt": exempt,
        "contrib": contrib,
    }
    pupils = np.array([h["pupils"] for h in GRID_HOUSEHOLDS], dtype=float)
    expected = pupils * 12_000 * 0.75 * max(statutory_rate(p), contrib)
    assert_close(calc(GRID_HOUSEHOLDS, p, "private_school_vat"), expected, str(p))
