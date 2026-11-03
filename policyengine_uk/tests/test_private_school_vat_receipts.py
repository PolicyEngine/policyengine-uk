"""School VAT is a share of receipt-calibrated VAT, not extra receipts.

Let G be household VAT on recorded consumption other than energy bills,
grossed up to VAT receipts net of energy-bill VAT, E VAT on energy bills
(domestic_energy_vat, not grossed up), P0 the baseline school charge
(baseline_private_school_vat) and s private school fees' official share of
VAT receipts (gov.simulation.vat.private_school_share_of_receipts). General
VAT is G x (1 - s) + E; private_school_vat counts the school charge.

Invariants, for any population and year, with the exemption at current law
or restored:

- non-negative: as 0 <= s < 1, the allocation never makes general VAT
  negative, so vat and vat + private_school_vat are non-negative wherever
  recorded consumption and energy bills are;
- national identity: weighted vat + private_school_vat is weighted G, less s
  times weighted G, plus weighted E and weighted P0. It equals weighted G + E
  when the population's school charge is s of its gross VAT, and restoring
  the exemption lowers it by exactly weighted P0;
- once: vat reads neither attendance nor fees, so school-specific reforms
  leave it unchanged household by household, and vat_change is zero at
  baseline.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

ALWAYS = "2010-01-01.2100-12-31"
STANDARD = "gov.hmrc.vat.standard_rate"
EXEMPT = "gov.hmrc.vat.private_school_fees_exempt"
CONTRIB = "gov.contrib.labour.private_school_vat"
LEGACY = "gov.simulation.microdata_vat_coverage"
FEES = "gov.simulation.private_school_vat.private_school_fees"
BASIS = "gov.simulation.private_school_vat.private_school_vat_basis"
FACTOR = 0.67 * 0.7
# HMRC's OBR-certified costing of VAT on private school fees (Autumn Budget
# 2024 Table 5.1, £m) and OBR cash-basis VAT receipts (October 2026 EFO
# detailed forecast tables, receipts, sheet 4.8, row 13, cells D13:H13, £m),
# by the model year of each fiscal year.
COSTING = {2025: 1_505, 2026: 1_560, 2027: 1_610, 2028: 1_665, 2029: 1_725}
RECEIPTS = {
    2025: 179_861.00,
    2026: 186_154.08,
    2027: 193_973.60,
    2028: 203_284.38,
    2029: 211_700.88,
}
# The share is zero before the 2025-26 model year and the 2029-30 value is
# held from then on.
OFFICIAL_SHARE = {
    2024: 0.0,
    **{year: COSTING[year] / RECEIPTS[year] for year in COSTING},
    2030: COSTING[2029] / RECEIPTS[2029],
    2031: COSTING[2029] / RECEIPTS[2029],
}
# Model values are float32; the parameter is rounded to six decimal places.
RTOL = 1e-6
SHARE_ATOL = 5e-7


def share(year):
    return system.parameters.gov.simulation.vat.private_school_share_of_receipts(year)


@pytest.mark.parametrize("year", sorted(OFFICIAL_SHARE))
def test_official_share_is_the_costing_over_receipts(year):
    assert share(year) == pytest.approx(OFFICIAL_SHARE[year], abs=SHARE_ATOL)


def simulation(
    year=2025, full=10_000, reduced=1_000, reforms=None, pupils=1, energy_vat=None
):
    changes = {
        FEES: {ALWAYS: 10_000},
        BASIS: {ALWAYS: 1},
        **{key: {ALWAYS: value} for key, value in (reforms or {}).items()},
    }
    people = {"adult": {"age": {year: 40}}}
    for i in range(pupils):
        people[f"pupil_{i}"] = {
            "age": {year: 10},
            "attends_private_school": {year: True},
        }
    household = {
        "members": list(people),
        "full_rate_vat_consumption": {year: full},
        "reduced_rate_vat_consumption": {year: reduced},
    }
    if energy_vat is not None:
        household["domestic_energy_vat"] = {year: energy_vat}
        household["baseline_domestic_energy_vat"] = {year: energy_vat}
    return Simulation(
        situation={
            "people": people,
            "benunits": {"family": {"members": list(people)}},
            "households": {"household": household},
        },
        reform=changes,
    )


def amount(sim, variable, year=2025):
    return float(sim.calculate(variable, year)[0])


@pytest.mark.parametrize("year", [2024, 2025, 2031])
@pytest.mark.parametrize("standard", [0, 0.2, 0.25])
@pytest.mark.parametrize("coverage", [None, 0.5])
def test_vat_is_gross_vat_less_the_official_share(year, standard, coverage):
    reforms = {STANDARD: standard}
    if coverage is not None:
        reforms[LEGACY] = coverage
    sim = simulation(year, reforms=reforms)
    keep = 1 - share(year)
    gross = (10_000 * standard + 1_000 * 0.05) / (coverage or FACTOR)
    assert amount(sim, "vat", year) == pytest.approx(gross * keep, abs=0.01)
    baseline_gross = (10_000 * 0.2 + 1_000 * 0.05) / FACTOR
    assert amount(sim, "baseline_vat", year) == pytest.approx(
        baseline_gross * keep, abs=0.01
    )
    # The fees bear the standard rate from 2025; each head responds to its
    # own base, so a standard-rate change moves the fees' VAT once.
    school = 0 if year < 2025 else 10_000 * standard
    baseline_school = 0 if year < 2025 else 10_000 * 0.2
    assert amount(sim, "private_school_vat", year) == pytest.approx(school)
    change = amount(sim, "vat_change", year) + amount(
        sim, "private_school_vat_change", year
    )
    expected = (gross - baseline_gross) * keep + school - baseline_school
    assert change == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize(
    "reforms,school,change",
    [
        ({EXEMPT: True}, 0, -2_000),
        ({CONTRIB: 0.2}, 2_000, 0),
        ({CONTRIB: 0.25}, 2_500, 500),
        ({STANDARD: 0.25, EXEMPT: True}, 0, -2_000),
    ],
)
def test_school_specific_reform_changes_only_the_school_head(reforms, school, change):
    sim = simulation(reforms=reforms)
    standard = reforms.get(STANDARD, 0.2)
    gross = (10_000 * standard + 1_000 * 0.05) / FACTOR
    assert amount(sim, "private_school_vat") == pytest.approx(school)
    assert amount(sim, "private_school_vat_change") == pytest.approx(change)
    assert amount(sim, "vat") == pytest.approx(gross * (1 - share(2025)), abs=0.01)


@pytest.mark.parametrize("exempt", [False, True])
def test_a_pupil_with_no_recorded_consumption_has_no_negative_vat(exempt):
    # This household's general VAT was -2,000 when its own school charge was
    # subtracted from its own VAT; restoring the exemption left it there.
    sim = simulation(full=0, reduced=0, reforms={EXEMPT: exempt})
    assert amount(sim, "vat") == 0
    assert amount(sim, "baseline_vat") == 0
    assert amount(sim, "vat_change") == 0
    assert amount(sim, "private_school_vat") == (0 if exempt else 2_000)
    assert amount(sim, "vat") + amount(sim, "private_school_vat") >= 0


@pytest.mark.parametrize("year", [2024, 2025, 2031])
@pytest.mark.parametrize("exempt", [False, True])
def test_energy_bill_vat_bears_no_school_share(year, exempt):
    # VAT on energy bills is added after grossing and is not a share of
    # receipts, so the school allocation comes out of the grossed-up amount
    # only, and a school reform leaves vat unchanged with energy VAT present.
    sim = simulation(year, reforms={EXEMPT: exempt}, energy_vat=300)
    keep = 1 - share(year)
    gross = (10_000 * 0.2 + 1_000 * 0.05) / FACTOR
    assert amount(sim, "vat", year) == pytest.approx(gross * keep + 300, abs=0.01)
    assert amount(sim, "baseline_vat", year) == pytest.approx(
        gross * keep + 300, abs=0.01
    )
    assert amount(sim, "vat_change", year) == pytest.approx(0, abs=0.01)


def test_vat_reads_neither_attendance_nor_fees():
    without = simulation(pupils=0)
    for pupils, fees in ((1, 10_000), (3, 5_000.10)):
        sim = simulation(pupils=pupils, reforms={FEES: fees})
        assert amount(sim, "vat") == amount(without, "vat")
        assert amount(sim, "vat_change") == 0


def test_published_microcosm_receipts_check_is_unchanged():
    # Rounded aggregate inputs published in docs/engineering/vat-coverage.md,
    # with energy bills split out: the standard-rated base and the energy-bill
    # VAT, which is added after grossing. Model year 2024 has no school charge
    # and no share to reallocate.
    sim = simulation(year=2024, full=396.15e9, reduced=0, energy_vat=1.99e9)
    combined = amount(sim, "vat", 2024) + amount(sim, "private_school_vat", 2024)
    expected = 0.2 * 396.15e9 / FACTOR + 1.99e9
    assert combined == pytest.approx(expected)
    assert combined / 170.994e9 == pytest.approx(1, rel=0.001)


def population_simulation(households, year=2025, reforms=None, fees=10_000.0):
    """One simulation of weighted households: weight, pupils, full and reduced."""
    people, benunits, hhs = {}, {}, {}
    for i, h in enumerate(households):
        members = [f"adult_{i}"]
        people[f"adult_{i}"] = {"age": {year: 45}}
        for j in range(h["pupils"]):
            people[f"pupil_{i}_{j}"] = {
                "age": {year: 7 + j},
                "attends_private_school": {year: True},
            }
            members.append(f"pupil_{i}_{j}")
        benunits[f"benunit_{i}"] = {"members": members}
        hhs[f"household_{i}"] = {
            "members": members,
            "household_weight": {year: h["weight"]},
            "full_rate_vat_consumption": {year: h["full"]},
            "reduced_rate_vat_consumption": {year: h.get("reduced", 0.0)},
        }
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": hhs},
        reform={
            FEES: {ALWAYS: fees},
            BASIS: {ALWAYS: 1},
            **{key: {ALWAYS: value} for key, value in (reforms or {}).items()},
        },
    )


def values(sim, year=2025):
    return {
        variable: np.asarray(sim.calculate(variable, year), dtype=float)
        for variable in (
            "household_weight",
            "vat",
            "baseline_vat",
            "vat_change",
            "private_school_vat",
            "baseline_private_school_vat",
        )
    }


def gross_vat(households):
    return (
        np.array([h["full"] * 0.2 + h.get("reduced", 0.0) * 0.05 for h in households])
        / FACTOR
    )


def weighted(weight, *amounts):
    return float(np.sum(weight * sum(amounts)))


def test_national_identity_on_a_small_weighted_population():
    s = share(2025)
    population = [
        {"weight": 1_000.0, "pupils": 0, "full": 100_000.0},
        {"weight": None, "pupils": 1, "full": 0.0},
        {"weight": 20.0, "pupils": 2, "full": 20_000.0, "reduced": 4_000.0},
    ]
    # Weight the pupil household without consumption so that the school
    # charge, 2,000 a pupil, is exactly the official share of the
    # population's gross VAT.
    others = gross_vat([population[0], population[2]])
    population[1]["weight"] = (
        s * (1_000 * others[0] + 20 * others[1]) - 20 * 2 * 2_000
    ) / 2_000
    weight = np.array([h["weight"] for h in population])
    gross = gross_vat(population)
    school = np.array([h["pupils"] for h in population]) * 2_000.0
    assert weighted(weight, school) == pytest.approx(s * weighted(weight, gross))

    baseline = values(population_simulation(population))
    np.testing.assert_allclose(baseline["vat"], gross * (1 - s), rtol=RTOL)
    np.testing.assert_array_equal(baseline["vat_change"], 0)
    combined = weighted(weight, baseline["vat"], baseline["private_school_vat"])
    # Current-law receipts are unchanged when the school charge is the
    # official share of gross VAT.
    assert combined == pytest.approx(weighted(weight, gross), rel=RTOL)

    # Restoring the exemption lowers receipts by the weighted baseline charge
    # and leaves general VAT alone.
    repeal = values(population_simulation(population, reforms={EXEMPT: True}))
    np.testing.assert_array_equal(repeal["vat"], baseline["vat"])
    np.testing.assert_array_equal(repeal["private_school_vat"], 0)
    repeal_combined = weighted(weight, repeal["vat"], repeal["private_school_vat"])
    assert combined - repeal_combined == pytest.approx(
        weighted(weight, school), rel=RTOL
    )


household = st.fixed_dictionaries(
    {
        "weight": st.floats(1, 5_000),
        "pupils": st.integers(0, 3),
        "full": st.one_of(st.just(0.0), st.floats(1_000, 150_000)),
        "reduced": st.one_of(st.just(0.0), st.floats(100, 30_000)),
    }
)


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    households=st.lists(household, min_size=1, max_size=4),
    year=st.integers(2024, 2030),
    fees=st.floats(1_000, 50_000),
)
@example(
    households=[{"weight": 1.0, "pupils": 1, "full": 0.0, "reduced": 0.0}],
    year=2025,
    fees=10_000.0,
)
def test_vat_is_never_negative_and_receipts_are_counted_once(households, year, fees):
    results = {
        scenario: values(population_simulation(households, year, reforms, fees), year)
        for scenario, reforms in (("baseline", {}), ("repeal", {EXEMPT: True}))
    }
    for scenario, result in results.items():
        assert (result["vat"] >= 0).all(), scenario
        assert (result["vat"] + result["private_school_vat"] >= 0).all(), scenario
    baseline, repeal = results["baseline"], results["repeal"]
    # Differential: G x (1 - s) from the inputs and the published shares.
    gross = gross_vat(households)
    np.testing.assert_allclose(
        baseline["vat"], gross * (1 - OFFICIAL_SHARE[year]), rtol=1e-5, atol=0.01
    )
    np.testing.assert_array_equal(baseline["vat_change"], 0)
    np.testing.assert_array_equal(repeal["vat"], baseline["vat"])
    np.testing.assert_array_equal(repeal["private_school_vat"], 0)
    weight = baseline["household_weight"]
    school = baseline["baseline_private_school_vat"]
    combined = weighted(weight, baseline["vat"], baseline["private_school_vat"])
    expected = weighted(weight, gross) * (1 - share(year)) + weighted(weight, school)
    assert combined == pytest.approx(expected, rel=1e-5, abs=0.01)
    repeal_combined = weighted(weight, repeal["vat"], repeal["private_school_vat"])
    assert combined - repeal_combined == pytest.approx(
        weighted(weight, school), rel=1e-5, abs=0.01
    )


GB_ELECTRICITY = "gov.hmrc.vat.domestic_electricity_rate.great_britain"
NI_ELECTRICITY = "gov.hmrc.vat.domestic_electricity_rate.northern_ireland"


def electricity_rate(region, year):
    # SI 2026/987 zero-rates domestic electricity in Great Britain from
    # 1 October 2026, and Budget 2026 extends that to 1 July 2027 and to
    # Northern Ireland from 1 April 2027. Model year 2026 has 178 of 365 days
    # at 5% in Great Britain and 360 in Northern Ireland; model year 2027 has
    # 280 of 366 in both. Every other year stays at 5%.
    if year == 2026:
        return 0.05 * (360 if region == "NORTHERN_IRELAND" else 178) / 365
    if year == 2027:
        return 0.05 * 280 / 366
    return 0.05


energy_households = st.fixed_dictionaries(
    {
        "weight": st.floats(1, 5_000),
        "pupils": st.integers(0, 3),
        "full": st.one_of(st.just(0.0), st.floats(1_000, 150_000)),
        "electricity": st.one_of(st.just(0.0), st.floats(100, 5_000)),
        "gas": st.one_of(st.just(0.0), st.floats(100, 5_000)),
        "region": st.sampled_from(["LONDON", "SCOTLAND", "NORTHERN_IRELAND"]),
    }
)


def energy_population(households, year, fees, reforms=None):
    """Weighted households with energy bills, as one simulation."""
    people, benunits, hhs = {}, {}, {}
    for i, h in enumerate(households):
        members = [f"adult_{i}"]
        people[f"adult_{i}"] = {"age": {year: 45}}
        for j in range(h["pupils"]):
            people[f"pupil_{i}_{j}"] = {
                "age": {year: 7 + j},
                "attends_private_school": {year: True},
            }
            members.append(f"pupil_{i}_{j}")
        benunits[f"benunit_{i}"] = {"members": members}
        hhs[f"household_{i}"] = {
            "members": members,
            "region": {year: h["region"]},
            "household_weight": {year: h["weight"]},
            "full_rate_vat_consumption": {year: h["full"]},
            "reduced_rate_vat_consumption": {year: 0.0},
            "electricity_consumption": {year: h["electricity"]},
            "gas_consumption": {year: h["gas"]},
        }
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": hhs},
        reform={
            FEES: {ALWAYS: fees},
            BASIS: {ALWAYS: 1},
            **{key: {ALWAYS: value} for key, value in (reforms or {}).items()},
        },
    )
    return {
        variable: np.asarray(sim.calculate(variable, year), dtype=float)
        for variable in (
            "household_weight",
            "vat",
            "vat_change",
            "domestic_energy_vat",
            "baseline_domestic_energy_vat",
            "private_school_vat",
            "baseline_private_school_vat",
        )
    }


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    households=st.lists(energy_households, min_size=1, max_size=4),
    year=st.integers(2024, 2030),
    fees=st.floats(1_000, 50_000),
)
@example(
    households=[
        {
            "weight": 1.0,
            "pupils": 1,
            "full": 0.0,
            "electricity": 1_050.0,
            "gas": 1_050.0,
            "region": "LONDON",
        }
    ],
    year=2027,
    fees=10_000.0,
)
def test_school_share_never_touches_energy_bill_vat(households, year, fees):
    # vat = G x (1 - s) + E with E from the statute (the bill net of the 5%
    # price basis, at the electricity and gas rates). Restoring the exemption
    # leaves vat unchanged, zero-rating electricity moves vat by exactly the
    # change in energy-bill VAT, and the national identity holds with E.
    s = OFFICIAL_SHARE[year]
    gross = np.array([h["full"] * 0.2 for h in households]) / FACTOR
    electricity = np.array(
        [
            h["electricity"] / 1.05 * electricity_rate(h["region"], year)
            for h in households
        ]
    )
    energy = electricity + np.array([h["gas"] / 1.05 * 0.05 for h in households])

    base = energy_population(households, year, fees)
    np.testing.assert_allclose(
        base["domestic_energy_vat"], energy, rtol=1e-5, atol=0.01
    )
    np.testing.assert_allclose(
        base["vat"], gross * (1 - s) + energy, rtol=1e-5, atol=0.01
    )
    np.testing.assert_allclose(base["vat_change"], 0, atol=0.01)

    repeal = energy_population(households, year, fees, {EXEMPT: True})
    np.testing.assert_array_equal(repeal["vat"], base["vat"])

    zero = energy_population(
        households, year, fees, {GB_ELECTRICITY: 0.0, NI_ELECTRICITY: 0.0}
    )
    energy_change = zero["domestic_energy_vat"] - zero["baseline_domestic_energy_vat"]
    np.testing.assert_allclose(energy_change, -electricity, rtol=1e-5, atol=0.01)
    np.testing.assert_allclose(zero["vat_change"], energy_change, rtol=1e-5, atol=0.01)
    np.testing.assert_array_equal(
        zero["private_school_vat"], base["private_school_vat"]
    )

    w = base["household_weight"]
    combined = weighted(w, base["vat"], base["private_school_vat"])
    expected = weighted(w, gross * (1 - s), energy, base["baseline_private_school_vat"])
    assert combined == pytest.approx(expected, rel=1e-5, abs=0.01)
