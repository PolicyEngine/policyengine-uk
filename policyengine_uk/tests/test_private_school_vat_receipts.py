"""School VAT is a partition of receipt-calibrated VAT, not extra receipts."""

import pytest

from policyengine_uk import Simulation

ALWAYS = "2010-01-01.2100-12-31"
STANDARD = "gov.hmrc.vat.standard_rate"
EXEMPT = "gov.hmrc.vat.private_school_fees_exempt"
CONTRIB = "gov.contrib.labour.private_school_vat"
LEGACY = "gov.simulation.microdata_vat_coverage"


def simulation(year=2025, full=10_000, reduced=1_000, reforms=None):
    changes = {
        "gov.simulation.private_school_vat.private_school_fees": {ALWAYS: 10_000},
        "gov.simulation.private_school_vat.private_school_vat_basis": {ALWAYS: 1},
        **{key: {ALWAYS: value} for key, value in (reforms or {}).items()},
    }
    return Simulation(
        situation={
            "people": {
                "adult": {"age": {year: 40}},
                "pupil": {
                    "age": {year: 10},
                    "attends_private_school": {year: True},
                },
            },
            "benunits": {"family": {"members": ["adult", "pupil"]}},
            "households": {
                "household": {
                    "members": ["adult", "pupil"],
                    "full_rate_vat_consumption": {year: full},
                    "reduced_rate_vat_consumption": {year: reduced},
                }
            },
        },
        reform=changes,
    )


def amount(sim, variable, year=2025):
    return float(sim.calculate(variable, year)[0])


@pytest.mark.parametrize("year", [2024, 2025, 2031])
@pytest.mark.parametrize("standard", [0, 0.2, 0.25])
@pytest.mark.parametrize("coverage", [None, 0.5])
def test_combined_vat_preserves_receipt_calibration(year, standard, coverage):
    reforms = {STANDARD: standard}
    if coverage is not None:
        reforms[LEGACY] = coverage
    sim = simulation(year, reforms=reforms)
    factor = 0.67 * 0.7 if coverage is None else coverage
    expected = (10_000 * standard + 1_000 * 0.05) / factor
    combined = amount(sim, "vat", year) + amount(sim, "private_school_vat", year)
    assert combined == pytest.approx(expected, abs=0.01)
    # The fee-rate response is already inside the receipt-calibrated total.
    baseline_total = (10_000 * 0.2 + 1_000 * 0.05) / (0.67 * 0.7)
    change = amount(sim, "vat_change", year) + amount(
        sim, "private_school_vat_change", year
    )
    assert change == pytest.approx(expected - baseline_total, abs=0.01)


@pytest.mark.parametrize(
    "reforms,school,change",
    [
        ({EXEMPT: True}, 0, -2_000),
        ({CONTRIB: 0.2}, 2_000, 0),
        ({CONTRIB: 0.25}, 2_500, 500),
        ({STANDARD: 0.25, EXEMPT: True}, 0, -2_500),
    ],
)
def test_school_specific_reform_changes_combined_receipts_once(reforms, school, change):
    sim = simulation(reforms=reforms)
    standard = reforms.get(STANDARD, 0.2)
    gross = (10_000 * standard + 1_000 * 0.05) / (0.67 * 0.7)
    assert amount(sim, "private_school_vat") == pytest.approx(school)
    assert amount(sim, "vat") + school == pytest.approx(gross + change, abs=0.01)


def test_sparse_calculator_inputs_do_not_create_extra_receipts():
    sim = simulation(full=0, reduced=0)
    assert amount(sim, "private_school_vat") == 2_000
    assert amount(sim, "vat") == -2_000
    assert amount(sim, "baseline_vat") == -2_000
    assert amount(sim, "vat_change") == 0


def test_published_microcosm_receipts_check_is_unchanged():
    # Rounded aggregate inputs published in docs/engineering/vat-coverage.md.
    sim = simulation(year=2024, full=396.15e9, reduced=25.02e9)
    combined = amount(sim, "vat", 2024) + amount(sim, "private_school_vat", 2024)
    expected = (0.2 * 396.15e9 + 0.05 * 25.02e9) / (0.67 * 0.7)
    assert combined == pytest.approx(expected)
    assert combined / 170.994e9 == pytest.approx(1, rel=0.004)
