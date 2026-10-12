"""Tests for the capital gains tax schedules added for issue #1858.

The schedule inputs (``capital_gains_badr``, ``capital_gains_residential_property``,
``capital_gains_carried_interest``) must leave ``capital_gains_tax`` bit for bit
unchanged when they are zero, and be charged at their own rates when they are
not. The per-case arithmetic lives in the YAML tests next to the variable; this
file proves the identity, the response plumbing and the parameter dates.
"""

import numpy as np
import pytest

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation
from policyengine_uk.model_api import Scenario, max_, min_

SCHEDULE_INPUTS = (
    "capital_gains_badr",
    "capital_gains_residential_property",
    "capital_gains_carried_interest",
)


def legacy_capital_gains_tax(sim, year):
    """The single-schedule formula as it stood before #1858, on the same arrays.

    Copied operation for operation so that any difference in the result is a
    difference in the new formula, not in the comparison.
    """
    hmrc = sim.tax_benefit_system.parameters(str(year)).gov.hmrc
    cgt = hmrc.cgt
    it = hmrc.income_tax

    def get(name):
        return sim.calculate(name, year).values

    personal_pension_band_extension = min_(
        get("personal_pension_contributions"),
        get("pension_contributions_relief"),
    )
    basic_rate_band_extension = (
        get("gift_aid_grossed_up") + personal_pension_band_extension
    )
    allowances_for_cgt_income = max_(
        0,
        get("allowances") - get("gift_aid") - personal_pension_band_extension,
    )
    taxable_income = max_(0, get("adjusted_net_income") - allowances_for_cgt_income)
    gains = max_(0, get("capital_gains"))
    aea = cgt.annual_exempt_amount
    gains_less_aea = max_(0, gains - aea)
    basic_rate_limit = it.rates.uk.thresholds[1] + basic_rate_band_extension
    remaining_basic_rate_band = max_(basic_rate_limit - taxable_income, 0)

    basic_rate_applicable_cg = min_(gains_less_aea, remaining_basic_rate_band)
    higher_and_add_rate_applicable_cg = max_(
        gains_less_aea - remaining_basic_rate_band, 0
    )
    higher_rate_limit = it.rates.uk.thresholds[2] + basic_rate_band_extension
    higher_rate_applicable_cg = min_(
        higher_and_add_rate_applicable_cg,
        higher_rate_limit - basic_rate_limit,
    )
    add_rate_applicable_cg = max_(
        higher_and_add_rate_applicable_cg - higher_rate_applicable_cg, 0
    )

    basic_rate_tax = basic_rate_applicable_cg * cgt.basic_rate
    higher_rate_tax = higher_rate_applicable_cg * cgt.higher_rate
    add_rate_tax = add_rate_applicable_cg * cgt.additional_rate

    return basic_rate_tax + higher_rate_tax + add_rate_tax


def assert_bit_identical_where_inputs_are_zero(sim, year):
    """The new formula reproduces the old one, bit for bit, at zero inputs."""
    new = sim.calculate("capital_gains_tax", year).values
    legacy = legacy_capital_gains_tax(sim, year)
    zero_inputs = np.ones_like(new, dtype=bool)
    for name in SCHEDULE_INPUTS:
        zero_inputs &= sim.calculate(name, year).values == 0
    assert zero_inputs.any()

    assert new.dtype == np.float32
    assert legacy.dtype == np.float32
    assert np.array_equal(new[zero_inputs], legacy[zero_inputs])
    new_bits = np.ascontiguousarray(new[zero_inputs]).view(np.uint32)
    legacy_bits = np.ascontiguousarray(legacy[zero_inputs]).view(np.uint32)
    assert np.array_equal(new_bits, legacy_bits)


INCOMES = [0, 5_000, 12_570, 20_000, 42_570, 50_270, 100_000, 125_140, 150_000, 500_000]
GAINS = [
    -50_000,
    -1,
    0,
    1,
    2_999,
    3_000,
    3_001,
    12_300,
    23_000,
    40_000,
    50_000,
    100_000,
    200_000,
    1_000_000,
    5_000_000,
]
YEARS = [2018, 2020, 2022, 2023, 2024, 2025, 2026, 2030]
VARIANTS = {
    "plain": {},
    "gift_aid": {"gift_aid": 5_000},
    "pension": {"employment_income": 52_570, "personal_pension_contributions": 10_000},
}


def grid_situation(year, extra=None):
    """One single-person household per (income, gains) pair."""
    people, benunits, households = {}, {}, {}
    for i, (income, gains) in enumerate(
        (income, gains) for income in INCOMES for gains in GAINS
    ):
        name = f"person_{i}"
        person = {
            "age": {year: 45},
            "adjusted_net_income": {year: income},
            "capital_gains": {year: gains},
        }
        for variable, value in (extra or {}).items():
            person[variable] = {year: value}
        people[name] = person
        benunits[f"benunit_{i}"] = {"members": [name]}
        households[f"household_{i}"] = {"members": [name]}
    return {"people": people, "benunits": benunits, "households": households}


def single_person(year, **variables):
    person = {"age": {year: 45}}
    for variable, value in variables.items():
        person[variable] = {year: value}
    return {
        "people": {"person": person},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


class TestZeroInputsAreBitIdentical:
    @pytest.mark.parametrize("variant", list(VARIANTS))
    @pytest.mark.parametrize("year", YEARS)
    def test_across_years_incomes_and_gains(self, year, variant):
        sim = Microsimulation(situation=grid_situation(year, VARIANTS[variant]))
        assert_bit_identical_where_inputs_are_zero(sim, year)

    @pytest.mark.parametrize(
        "changes",
        [
            {
                "gov.hmrc.cgt.basic_rate": {"2025": 0.20},
                "gov.hmrc.cgt.higher_rate": {"2025": 0.40},
                "gov.hmrc.cgt.additional_rate": {"2025": 0.45},
            },
            {"gov.hmrc.cgt.annual_exempt_amount": {"2025": 12_300.33}},
        ],
        ids=["equalised_rates", "fractional_aea"],
    )
    def test_under_reforms(self, changes):
        sim = Microsimulation(
            situation=grid_situation(2025),
            scenario=Scenario(parameter_changes=changes),
        )
        assert_bit_identical_where_inputs_are_zero(sim, 2025)

    @pytest.mark.microsimulation
    def test_on_the_default_dataset(self):
        """The dataset carries no schedule inputs yet, so nothing may move.

        conftest skips microsimulation tests when no default dataset is set.
        """
        sim = Microsimulation()
        for year in (2024, 2025, 2026):
            assert_bit_identical_where_inputs_are_zero(sim, year)


class TestResponsePlumbing:
    YEAR = 2026

    def test_residential_rate_reform_moves_only_residential_gains(self):
        """The realisation response sees reforms on the new schedules.

        A landlord whose gains are all residential property faces a higher
        marginal rate under a residential-rate rise; a person with only
        main-rate gains sees no change at all.
        """
        year = self.YEAR
        situation = {
            "people": {
                "landlord": {
                    "age": {year: 45},
                    "employment_income": {year: 100_000},
                    "capital_gains": {year: 100_000},
                    "capital_gains_residential_property": {year: 100_000},
                },
                "trader": {
                    "age": {year: 45},
                    "employment_income": {year: 100_000},
                    "capital_gains": {year: 100_000},
                },
            },
            "benunits": {
                "landlord_bu": {"members": ["landlord"]},
                "trader_bu": {"members": ["trader"]},
            },
            "households": {
                "landlord_hh": {"members": ["landlord"]},
                "trader_hh": {"members": ["trader"]},
            },
        }
        changes = {
            "gov.hmrc.cgt.residential_property.higher_rate": {str(year): 0.30},
            "gov.hmrc.cgt.residential_property.additional_rate": {str(year): 0.30},
            "gov.simulation.capital_gains_responses.mtr_elasticity": {str(year): -0.5},
        }
        sim = Microsimulation(
            situation=situation, scenario=Scenario(parameter_changes=changes)
        )
        change = sim.calculate("relative_capital_gains_mtr_change", year).values
        landlord, trader = change
        assert landlord > 0
        assert trader == 0

        gains = sim.calculate("capital_gains", year).values
        assert gains[0] < 100_000
        assert gains[1] == 100_000

    def test_marginal_rate_is_share_weighted_across_schedules(self):
        """Half carried interest at 32% and half main-rate gains at 24%."""
        year = 2025
        sim = Microsimulation(
            situation=single_person(
                year,
                employment_income=150_000,
                capital_gains=100_000,
                capital_gains_carried_interest=50_000,
            )
        )
        mtr = sim.calculate("marginal_tax_rate_on_capital_gains", year).values[0]
        assert mtr == pytest.approx(0.5 * 0.32 + 0.5 * 0.24, abs=1e-3)

    def test_response_scales_the_schedule_components(self):
        """A response that shrinks capital_gains shrinks the taxed residential gains."""
        year = self.YEAR
        situation = single_person(
            year,
            employment_income=100_000,
            capital_gains=100_000,
            capital_gains_residential_property=100_000,
        )
        changes = {
            "gov.hmrc.cgt.residential_property.higher_rate": {str(year): 0.40},
            "gov.hmrc.cgt.residential_property.additional_rate": {str(year): 0.40},
            "gov.simulation.capital_gains_responses.elasticity": {str(year): 1.0},
        }
        reformed = Microsimulation(
            situation=situation, scenario=Scenario(parameter_changes=changes)
        )
        gains = reformed.calculate("capital_gains", year).values[0]
        tax = reformed.calculate("capital_gains_tax", year).values[0]
        assert 0 < gains < 100_000
        # Every realised pound is residential, so the tax is 40% of the gains
        # above the annual exempt amount: the component followed the response.
        assert tax == pytest.approx((gains - 3_000) * 0.40, rel=1e-4)


class TestEqualisationReforms:
    """What a reform must set to reach every schedule.

    The main rates no longer cover residential property, carried interest or
    relief gains, so a reform that moves only them leaves the other schedules
    at current law. Taxing every gain at income tax rates means setting the
    other two schedules' rates as well and switching the relief off through
    its lifetime limit, since the relief rate is band-independent.
    """

    YEAR = 2025
    MAIN_RATES_ONLY = {
        "gov.hmrc.cgt.basic_rate": {"2025": 0.20},
        "gov.hmrc.cgt.higher_rate": {"2025": 0.40},
        "gov.hmrc.cgt.additional_rate": {"2025": 0.45},
    }
    EVERY_SCHEDULE = {
        **MAIN_RATES_ONLY,
        "gov.hmrc.cgt.residential_property.basic_rate": {"2025": 0.20},
        "gov.hmrc.cgt.residential_property.higher_rate": {"2025": 0.40},
        "gov.hmrc.cgt.residential_property.additional_rate": {"2025": 0.45},
        "gov.hmrc.cgt.carried_interest.basic_rate": {"2025": 0.20},
        "gov.hmrc.cgt.carried_interest.higher_rate": {"2025": 0.40},
        "gov.hmrc.cgt.carried_interest.additional_rate": {"2025": 0.45},
        "gov.hmrc.cgt.badr.lifetime_limit": {"2025": 0},
    }
    SCHEDULES = (None, *SCHEDULE_INPUTS)

    def tax(self, schedule, changes=None):
        variables = {"employment_income": 100_000, "capital_gains": 100_000}
        if schedule is not None:
            variables[schedule] = 100_000
        kwargs = {"scenario": Scenario(parameter_changes=changes)} if changes else {}
        sim = Microsimulation(situation=single_person(self.YEAR, **variables), **kwargs)
        return float(sim.calculate("capital_gains_tax", self.YEAR).values[0])

    def test_main_rate_reform_leaves_the_other_schedules_at_current_law(self):
        baseline = {s: self.tax(s) for s in self.SCHEDULES}
        reformed = {s: self.tax(s, self.MAIN_RATES_ONLY) for s in self.SCHEDULES}

        # 97,000 above the AEA, all above the basic rate band: 87,440 at 40%
        # and 9,560 at 45%.
        assert reformed[None] == pytest.approx(39_278)
        for schedule in SCHEDULE_INPUTS:
            assert reformed[schedule] == baseline[schedule], schedule

    def test_setting_every_schedule_taxes_every_gain_alike(self):
        reformed = {s: self.tax(s, self.EVERY_SCHEDULE) for s in self.SCHEDULES}

        for schedule in self.SCHEDULES:
            assert reformed[schedule] == pytest.approx(39_278), schedule


class TestScheduleParameters:
    """Dates and values of the new gov.hmrc.cgt parameters by fiscal year."""

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("badr.rate", {2024: 0.10, 2025: 0.14, 2026: 0.18}),
            ("badr.lifetime_limit", {2019: 10_000_000, 2020: 1_000_000}),
            ("residential_property.basic_rate", {2023: 0.18, 2024: 0.18}),
            ("residential_property.higher_rate", {2023: 0.28, 2024: 0.24}),
            ("carried_interest.basic_rate", {2024: 0.18, 2025: 0.32}),
            ("carried_interest.higher_rate", {2024: 0.28, 2025: 0.32}),
        ],
    )
    def test_values_by_fiscal_year(self, path, expected):
        system = CountryTaxBenefitSystem()
        for year, value in expected.items():
            node = system.get_parameters_at_instant(str(year)).gov.hmrc.cgt
            for part in path.split("."):
                node = getattr(node, part)
            # Exact: none of these is blended across a fiscal year.
            assert node == value, (path, year, node)

    def test_new_parameters_are_not_blended(self):
        system = CountryTaxBenefitSystem()
        cgt = system.parameters.gov.hmrc.cgt
        for schedule in (cgt.badr, cgt.residential_property, cgt.carried_interest):
            for parameter in schedule.children.values():
                assert not (parameter.metadata or {}).get("fiscal_year_blend"), (
                    parameter.name
                )

    @pytest.mark.parametrize("schedule", ["residential_property", "carried_interest"])
    def test_additional_rate_equals_higher_rate_in_law(self, schedule):
        system = CountryTaxBenefitSystem()
        for year in range(2015, 2031):
            node = getattr(
                system.get_parameters_at_instant(str(year)).gov.hmrc.cgt, schedule
            )
            assert node.additional_rate == node.higher_rate, (schedule, year)
