"""UC financial observations, complete overrides, and countable property.

Regulations 18, 49 and 72 provide the capital limit, property valuation and
tariff. Equal shares per claimant/partner adult are a modelling convention
for household assets whose beneficial ownership is unobserved. Property
allocation is independent of other units' financial reports and depends only
on claimant and partner adult counts. The residual financial pool is shared
among units without a report, so another unit's report can change that pool
and their capital. This is an inherited convention. These cases assume the
properties incur sale expenses and have no Schedule 10 disregard. An explicit
uc_reported_capital replaces the ordinary sources before regulation 77 company
substitution.
"""

from copy import deepcopy

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
PROPERTIES = (
    "other_residential_property_value",
    "non_residential_property_value",
)
DEBTS = (
    "other_residential_property_secured_debt",
    "non_residential_property_secured_debt",
)
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    database=None,
)


def _annual(value):
    return value if isinstance(value, dict) else {YEAR: value}


def _situation(units=None, household=None):
    """Build one household, retaining stable person and benefit-unit ids."""
    units = [{"financial": 0}] if units is None else units
    people, benunits, members = {}, {}, []
    for i, unit in enumerate(units):
        names = []
        for j in range(unit.get("adults", 1)):
            name = f"p{i}_{j}"
            people[name] = {
                "age": {YEAR: 30},
                "is_claimant_or_partner": {YEAR: True},
            }
            names.append(name)
        for j in range(unit.get("children", 0)):
            name = f"c{i}_{j}"
            people[name] = {
                "age": {YEAR: 10},
                "is_claimant_or_partner": {YEAR: False},
            }
            names.append(name)
        benunit = {
            "members": names,
            "would_claim_uc": {YEAR: unit.get("claims_uc", True)},
        }
        if "financial" in unit:
            benunit["benunit_reported_capital"] = _annual(unit["financial"])
        if "override" in unit:
            benunit["uc_reported_capital"] = _annual(unit["override"])
        benunits[f"b{i}"] = benunit
        members.extend(names)
    return {
        "people": people,
        "benunits": benunits,
        "households": {
            "h": {
                "members": members,
                **{name: _annual(value) for name, value in (household or {}).items()},
            }
        },
    }


def _values(simulation, variable="uc_assessable_capital", year=YEAR):
    return np.asarray(simulation.calculate(variable, year))


@pytest.mark.parametrize("property_variable", PROPERTIES)
def test_reported_financial_zero_keeps_fifty_thousand_pound_property(property_variable):
    simulation = Simulation(
        situation=_situation(household={property_variable: 50_000, "savings": 0})
    )
    assert _values(simulation)[0] == 45_000
    assert not _values(simulation, "is_uc_eligible")[0]
    assert _values(simulation, "universal_credit")[0] == 0


@pytest.mark.parametrize(
    "household",
    [
        {"other_residential_property_value": 10_000},
        {"non_residential_property_value": 10_000},
        {
            "other_residential_property_value": 3_000,
            "non_residential_property_value": 7_000,
        },
    ],
)
def test_financial_observation_and_property_are_both_counted(household):
    simulation = Simulation(situation=_situation([{"financial": 6_000}], household))
    assert _values(simulation)[0] == 15_000
    assert _values(simulation, "is_uc_eligible")[0]
    assert _values(simulation, "uc_tariff_income")[0] == pytest.approx(36 * 4.35 * 12)
    assert _values(simulation, "universal_credit")[0] == pytest.approx(
        _values(simulation, "uc_standard_allowance")[0] - 36 * 4.35 * 12
    )


@pytest.mark.parametrize("override", [0, 2_000, 20_000])
def test_explicit_complete_override_replaces_financial_and_property_capital(override):
    situation = _situation(
        [{"financial": 6_000, "override": override}],
        {"savings": 50_000, "other_residential_property_value": 50_000},
    )
    situation["people"]["p0_0"]["lifetime_isa_balance"] = {YEAR: 30_000}
    simulation = Simulation(situation=situation)
    assert _values(simulation)[0] == override
    if override == 0:
        assert _values(simulation, "universal_credit")[0] == pytest.approx(
            _values(simulation, "uc_standard_allowance")[0]
        )


def test_explicit_zero_override_still_includes_regulation_77_company_capital():
    situation = _situation(
        [{"financial": 6_000, "override": 0}],
        {"savings": 12_000, "other_residential_property_value": 40_000},
    )
    situation["people"]["p0_0"].update(
        {
            "stands_as_sole_owner_or_partner_of_company": {YEAR: True},
            "owned_company_carries_on_property_business": {YEAR: True},
            "owned_company_capital": {YEAR: 8_000},
        }
    )
    simulation = Simulation(situation=situation)
    # The override replaces the ordinary financial/property assessment;
    # regulation 77 then adds the owner's £8k of company capital.
    assert _values(simulation, "uc_company_capital")[0] == 8_000
    assert _values(simulation)[0] == 8_000


def test_financial_observation_does_not_double_count_savings_investments_or_lisa():
    situation = _situation(
        [{"financial": 6_000}], {"savings": 50_000, "corporate_wealth": 30_000}
    )
    situation["people"]["p0_0"]["lifetime_isa_balance"] = {YEAR: 30_000}
    simulation = Simulation(situation=situation)
    assert _values(simulation)[0] == 6_000
    assert _values(simulation, "uc_tariff_income")[0] == 0


def test_property_is_allocated_across_all_claimant_and_partner_adults():
    simulation = Simulation(
        situation=_situation(
            [
                {"adults": 2, "financial": 0, "children": 2},
                {"financial": 0, "claims_uc": False},
            ],
            {"other_residential_property_value": 12_000},
        )
    )
    np.testing.assert_allclose(_values(simulation), [7_200, 3_600])
    assert _values(simulation).sum() == pytest.approx(10_800)


@pytest.mark.parametrize("complete_override", [0, 50_000])
def test_mixed_household_keeps_financial_and_property_pools_separate(complete_override):
    simulation = Simulation(
        situation=_situation(
            [
                {"adults": 2, "override": complete_override},
                {"financial": 6_000},
                {"financial": -1},
            ],
            {"savings": 12_000, "other_residential_property_value": 40_000},
        )
    )
    # Complete override consumes its £18k conventional property share. Its
    # unknown financial/property composition never reduces the financial pool.
    np.testing.assert_allclose(_values(simulation), [complete_override, 15_000, 15_000])
    assert _values(simulation)[1:].sum() - 6_000 - 6_000 == pytest.approx(18_000)


@pytest.mark.parametrize("other_financial", [-1, 0, 50_000])
def test_unrelated_financial_reports_do_not_change_property_ownership(other_financial):
    simulation = Simulation(
        situation=_situation(
            [{"financial": 0}, {"financial": other_financial}],
            {"other_residential_property_value": 20_000},
        )
    )
    assert _values(simulation)[0] == 9_000
    assert _values(simulation)[1] == pytest.approx(9_000 + max(0, other_financial))


@pytest.mark.parametrize(
    "reports,expected",
    [([-1, -1], [6_000, 6_000]), ([-1, 0], [12_000, 0])],
    ids=["both-missing", "second-reports-zero"],
)
def test_inherited_residual_financial_sharing_intentionally_depends_on_other_reports(
    reports, expected
):
    simulation = Simulation(
        situation=_situation(
            [{"financial": report} for report in reports],
            {"savings": 12_000},
        )
    )
    # With no reports, two adults share £12k equally. A zero report removes
    # the second unit from the residual denominator without reducing the
    # pool, so the first unit receives all £12k. This convention is intended.
    np.testing.assert_allclose(_values(simulation), expected)


def test_inherited_financial_sharing_intentionally_adds_to_property_share_change():
    household = {"savings": 12_000, "other_residential_property_value": 40_000}
    alone = Simulation(situation=_situation([{"financial": -1}], household))
    with_reporting_unit = Simulation(
        situation=_situation([{"financial": -1}, {"financial": 6_000}], household)
    )
    # Alone: £12k financial proxy + £40k * 90% property = £48k.
    # With the reporting adult: (£12k - £6k) financial proxy + £36k / 2
    # property = £24k. The reporting unit also has £6k + £18k = £24k.
    np.testing.assert_allclose(_values(alone), [48_000])
    np.testing.assert_allclose(_values(with_reporting_unit), [24_000, 24_000])
    # The intended £24k fall includes £6k from the inherited residual pool
    # as well as the £18k change in the claimant's property share.
    assert _values(alone)[0] - _values(with_reporting_unit)[0] == 24_000


def test_reporting_a_conventional_financial_share_leaves_other_units_unchanged():
    household = {"savings": 12_000, "other_residential_property_value": 12_000}
    missing = Simulation(situation=_situation([{}, {}], household))
    observed = Simulation(situation=_situation([{"financial": 6_000}, {}], household))
    np.testing.assert_allclose(_values(missing), [11_400, 11_400])
    np.testing.assert_allclose(_values(observed), _values(missing))


@pytest.mark.parametrize("financial", [None, -1])
def test_missing_financial_and_spi_style_inputs_retain_the_financial_proxy(financial):
    # SPI synthetic units have no FRS financial observation. A missing column
    # and the explicit -1 sentinel must retain the same proxy calculation.
    unit = {} if financial is None else {"financial": financial}
    situation = _situation(
        [unit],
        {
            "savings": 4_000,
            "corporate_wealth": 2_000,
            "other_residential_property_value": 10_000,
        },
    )
    situation["people"]["p0_0"]["lifetime_isa_balance"] = {YEAR: 4_000}
    assert _values(Simulation(situation=situation))[0] == 18_000


@pytest.mark.parametrize("financial", [-1, 0, 6_000])
def test_occupied_main_home_is_excluded(financial):
    simulation = Simulation(
        situation=_situation(
            [{"financial": financial}],
            {"main_residence_value": 500_000, "savings": 0},
        )
    )
    assert _values(simulation)[0] == max(0, financial)


@pytest.mark.parametrize(
    "property_variable,debt_variable", list(zip(PROPERTIES, DEBTS))
)
@pytest.mark.parametrize("debt,expected", [(0, 9_000), (2_000, 7_000), (20_000, 0)])
def test_property_sale_expenses_precede_secured_debt_and_zero_floor(
    property_variable, debt_variable, debt, expected
):
    simulation = Simulation(
        situation=_situation(household={property_variable: 10_000, debt_variable: debt})
    )
    assert _values(simulation)[0] == expected


def test_secured_debt_on_one_property_component_does_not_reduce_the_other():
    simulation = Simulation(
        situation=_situation(
            household={
                "other_residential_property_value": 10_000,
                "other_residential_property_secured_debt": 20_000,
                "non_residential_property_value": 10_000,
            }
        )
    )
    assert _values(simulation)[0] == 9_000


def test_property_is_valued_in_the_assessment_year():
    simulation = Simulation(
        situation=_situation(
            [{"financial": {2025: 0, 2026: 0}}],
            {
                "other_residential_property_value": {2025: 10_000, 2026: 20_000},
                "other_residential_property_secured_debt": {2025: 1_000, 2026: 2_000},
            },
        )
    )
    assert _values(simulation, year=2025)[0] == 8_000
    assert _values(simulation, year=2026)[0] == 16_000
    assert _values(simulation, year="2026-01")[0] == 16_000


@pytest.mark.parametrize(
    "capital,tariff_steps,eligible",
    [
        (6_000, 0, True),
        (6_001, 1, True),
        (6_250, 1, True),
        (6_251, 2, True),
        (16_000, 40, True),
        (16_001, 0, False),
    ],
)
@pytest.mark.parametrize(
    "property_value", [0, 5_000], ids=["cash-only", "with-property"]
)
def test_tariff_boundaries_for_cash_and_valued_property(
    capital, tariff_steps, eligible, property_value
):
    # Only the property incurs sale expenses: do not reduce cash by 10%.
    financial = capital - property_value * 0.9
    simulation = Simulation(
        situation=_situation(
            [{"financial": financial}],
            {"other_residential_property_value": property_value},
        )
    )
    assert _values(simulation)[0] == capital
    assert bool(_values(simulation, "is_uc_eligible")[0]) is eligible
    assert _values(simulation, "uc_tariff_income")[0] == pytest.approx(
        tariff_steps * 4.35 * 12
    )


@PROPERTY_SETTINGS
@given(
    financial=st.sampled_from([-1, 0, 6_000]),
    source=st.sampled_from(
        [
            "financial",
            "savings",
            "corporate_wealth",
            "lifetime_isa_balance",
            *PROPERTIES,
        ]
    ),
    amount=st.integers(0, 50_000),
    increment=st.integers(0, 50_000),
)
def test_assessable_capital_never_falls_when_a_countable_asset_increases(
    financial, source, amount, increment
):
    baseline = _situation(
        [{"financial": financial}, {"financial": -1}],
        {"savings": 10_000, "other_residential_property_value": 10_000},
    )
    if source == "financial":
        target = baseline["benunits"]["b0"]
        input_variable = "benunit_reported_capital"
    elif source == "lifetime_isa_balance":
        target = baseline["people"]["p0_0"]
        input_variable = source
    else:
        target = baseline["households"]["h"]
        input_variable = source
    target[input_variable] = {YEAR: amount}
    higher = deepcopy(baseline)
    if source == "financial":
        higher_target = higher["benunits"]["b0"]
    elif source == "lifetime_isa_balance":
        higher_target = higher["people"]["p0_0"]
    else:
        higher_target = higher["households"]["h"]
    higher_target[input_variable] = {YEAR: amount + increment}
    low_capital = _values(Simulation(situation=baseline))
    high_capital = _values(Simulation(situation=higher))
    # An observed financial increase can reduce another unit's residual
    # financial proxy; monotonicity applies to the owner of that observation.
    if source == "financial":
        assert high_capital[0] >= low_capital[0]
    else:
        assert np.all(high_capital >= low_capital - 0.01)


@PROPERTY_SETTINGS
@given(
    adult_counts=st.lists(st.integers(1, 2), min_size=1, max_size=4),
    residential=st.integers(0, 100_000),
    non_residential=st.integers(0, 100_000),
    override_first=st.booleans(),
)
def test_property_allocation_conserves_value_including_complete_override_shares(
    adult_counts, residential, non_residential, override_first
):
    units = [{"adults": adults, "financial": 0} for adults in adult_counts]
    if override_first:
        units[0]["override"] = 0
    simulation = Simulation(
        situation=_situation(
            units,
            {
                "other_residential_property_value": residential,
                "non_residential_property_value": non_residential,
            },
        )
    )
    total_property = (residential + non_residential) * 0.9
    expected = np.asarray(adult_counts) / sum(adult_counts) * total_property
    consumed = expected[0] if override_first else 0
    if override_first:
        expected[0] = 0
    assessed = _values(simulation)
    np.testing.assert_allclose(assessed, expected, atol=0.02)
    assert assessed.sum() + consumed == pytest.approx(total_property, abs=0.03)


@PROPERTY_SETTINGS
@given(
    reports=st.lists(st.sampled_from([-1, 0, 6_000]), min_size=3, max_size=3),
    property_value=st.integers(0, 100_000),
    order=st.permutations([0, 1, 2]),
)
def test_capital_is_independent_of_person_and_benefit_unit_row_order(
    reports, property_value, order
):
    situation = _situation(
        [
            {"adults": 2, "financial": reports[0]},
            {"financial": reports[1]},
            {"financial": reports[2], "override": 0},
        ],
        {"savings": 12_000, "other_residential_property_value": property_value},
    )
    permuted = deepcopy(situation)
    permuted["benunits"] = {f"b{i}": permuted["benunits"][f"b{i}"] for i in order}
    for unit in permuted["benunits"].values():
        unit["members"] = list(reversed(unit["members"]))
    permuted["people"] = dict(reversed(list(permuted["people"].items())))
    permuted["households"]["h"]["members"].reverse()
    baseline = dict(
        zip(situation["benunits"], _values(Simulation(situation=situation)))
    )
    reordered = dict(zip(permuted["benunits"], _values(Simulation(situation=permuted))))
    for unit in baseline:
        assert reordered[unit] == pytest.approx(baseline[unit])


@pytest.mark.parametrize("complete_override", [0, 20_000])
@pytest.mark.parametrize(
    "financial_report", [None, -1, 10_000], ids=["omitted", "missing", "observed"]
)
def test_complete_override_company_holding_cannot_leak_into_missing_unit_pool(
    complete_override, financial_report
):
    owner_unit = {"override": complete_override}
    if financial_report is not None:
        owner_unit["financial"] = financial_report
    situation = _situation(
        [owner_unit, {"financial": -1}],
        {"corporate_wealth": 10_000, "savings": 6_000},
    )
    situation["people"]["p0_0"].update(
        {
            "stands_as_sole_owner_or_partner_of_company": {YEAR: True},
            "owned_company_carries_on_property_business": {YEAR: True},
            "owned_company_holding_value": {YEAR: 10_000},
            "owned_company_capital": {YEAR: 0},
        }
    )
    simulation = Simulation(situation=situation)
    assert _values(simulation, "uc_company_owner_treatment_applies")[0]
    assert _values(simulation, "uc_company_holding_disregard")[0] == 10_000
    assert _values(simulation, "uc_company_capital")[0] == 0
    # An observed financial report already removes the owner's holding from
    # the financial pool. Without one, remove it separately even when the
    # owner has a complete override; that override's decomposition is unknown.
    expected_pool_disregard = 0 if financial_report == 10_000 else 10_000
    assert (
        _values(simulation, "household_uc_pool_company_holdings")[0]
        == expected_pool_disregard
    )
    np.testing.assert_allclose(
        _values(simulation),
        [max(0, complete_override - 10_000), 6_000],
    )
