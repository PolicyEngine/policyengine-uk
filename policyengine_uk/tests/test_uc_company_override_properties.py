"""Exhaustive MOCK company-override conservation and residual-pool properties.

A complete override describes capital before regulation 77 substitution. Its
owner's holding must leave the financial pool once: through that override,
with a floor at its share of one household corporate-wealth budget. Dependants
own their holdings separately. The independent savings floor and accounting
identities cover inconsistent proxy observations as well as compatible inputs.
Regulation 77 still uses the original holding in its owner's own assessment.
"""

from itertools import product

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
# corporate_wealth is valued at 90% for the expenses of sale (UC Regs 2013
# reg. 49(1)(a)); disregarded holdings inside it leave the pool at that value.
SHARE_VALUE = 0.9
LAYOUTS = {
    "one-owner": ((10_000,), (), ()),
    "two-owners-one-unit": ((4_000, 6_000), (), ()),
    "claimant-and-dependant": ((6_000,), (4_000,), ()),
    "owners-in-separate-units": ((6_000,), (), (4_000,)),
}
OTHER_REPORTS = (
    {},
    {"financial": 6_000},
    {"override": 0},
    {"override": 4_000},
    {"override": 12_000},
)


def _company_person(holding=0, dependant=False):
    person = {
        "age": {YEAR: 10 if dependant else 30},
        "is_claimant_or_partner": {YEAR: not dependant},
    }
    if holding:
        person.update(
            {
                "stands_as_sole_owner_or_partner_of_company": {YEAR: True},
                "owned_company_carries_on_property_business": {YEAR: True},
                "owned_company_holding_value": {YEAR: holding},
                "owned_company_capital": {YEAR: 0},
            }
        )
    return person


def _grid(layout):
    """Combine 1,280 independent three-unit households in one simulation."""
    people, units, households, cases = {}, {}, {}, []
    first_holdings, dependant_holdings, second_holdings = LAYOUTS[layout]
    claimant_holdings = (sum(first_holdings), sum(second_holdings), 0)
    for index, (
        override,
        financial,
        corporate,
        savings,
        other,
        missing_adults,
    ) in enumerate(
        product(
            (0, 4_000, 10_000, 20_000),
            (None, -1, 4_000, 10_000),
            (0, 4_000, 10_000, 20_000),
            (6_000, 20_000),
            OTHER_REPORTS,
            (1, 2),
        )
    ):
        prefix = f"h{index}"
        specs = [{"override": override}, other, {}]
        if financial is not None:
            specs[0]["financial"] = financial
        members = []
        adult_counts = (len(first_holdings), 1, missing_adults)
        for unit_index, (spec, adults, holdings) in enumerate(
            zip(specs, adult_counts, (first_holdings, second_holdings, ()))
        ):
            names = []
            for adult_index in range(adults):
                name = f"{prefix}_u{unit_index}_a{adult_index}"
                holding = holdings[adult_index] if adult_index < len(holdings) else 0
                people[name] = _company_person(holding)
                names.append(name)
            if unit_index == 0:
                for child_index, holding in enumerate(dependant_holdings):
                    name = f"{prefix}_child{child_index}"
                    people[name] = _company_person(holding, dependant=True)
                    names.append(name)
            unit = {"members": names, "would_claim_uc": {YEAR: True}}
            if "financial" in spec:
                unit["benunit_reported_capital"] = {YEAR: spec["financial"]}
            if "override" in spec:
                unit["uc_reported_capital"] = {YEAR: spec["override"]}
            units[f"{prefix}_u{unit_index}"] = unit
            members.extend(names)
        households[prefix] = {
            "members": members,
            "savings": {YEAR: savings},
            "corporate_wealth": {YEAR: corporate},
        }
        cases.append(
            (
                specs,
                adult_counts,
                claimant_holdings,
                sum(dependant_holdings),
                corporate,
                savings,
            )
        )
    return {"people": people, "benunits": units, "households": households}, cases


@pytest.mark.parametrize("layout", LAYOUTS)
def test_company_overrides_conserve_capital_and_keep_holdings_out_of_other_units(
    layout,
):
    situation, cases = _grid(layout)
    simulation = Simulation(situation=situation)
    assessed = np.asarray(simulation.calculate("uc_assessable_capital", YEAR)).reshape(
        -1, 3
    )
    assert np.all(simulation.calculate("uc_company_capital", YEAR) == 0)
    for row, (specs, adults, holdings, dependants, corporate, savings) in zip(
        assessed, cases
    ):
        # The pool counts corporate_wealth at 90% (reg. 49(1)(a)), and holdings
        # inside it leave the pool at that value.
        pool = SHARE_VALUE * corporate + savings
        missing = [
            "override" not in spec and spec.get("financial", -1) < 0 for spec in specs
        ]
        explicit = [
            spec.get("override", max(0, spec.get("financial", -1))) for spec in specs
        ]
        # Invalid holdings are bounded per person, before grouping into units.
        # Allocate one budget by those ownership shares; never recap a route.
        bounded_holdings = [
            sum(min(corporate, value) for value in group)
            for group in (LAYOUTS[layout][0], LAYOUTS[layout][2], ())
        ]
        bounded_dependants = sum(min(corporate, value) for value in LAYOUTS[layout][1])
        total_holdings = sum(bounded_holdings) + bounded_dependants
        budget = min(corporate, total_holdings)
        scale = budget / total_holdings if total_holdings else 0
        market_holdings = [holding * scale for holding in bounded_holdings]
        effective_holdings = [SHARE_VALUE * holding for holding in market_holdings]
        # A recorded financial total holds its owners' holdings at full value;
        # the pool counts them at 90% (reg. 49(1)(a)), so the report consumes
        # its part beyond the holdings in full and the holdings at 90%. Like an
        # override, a report below the holdings still consumes them: a report
        # of 4,000 against a 10,000 holding consumes 9,000.
        explicit_consumption = sum(
            spec["override"]
            if "override" in spec
            else max(0, spec["financial"] - market) + SHARE_VALUE * market
            if spec.get("financial", -1) >= 0
            else 0
            for spec, market in zip(specs, market_holdings)
        )
        extra_holding_draw = SHARE_VALUE * bounded_dependants * scale + sum(
            holding
            if absent
            else max(0, holding - spec["override"])
            if "override" in spec
            else 0
            for holding, spec, absent in zip(effective_holdings, specs, missing)
        )
        residual = max(0, pool - explicit_consumption - extra_holding_draw)
        missing_capital = sum(
            capital for capital, absent in zip(row, missing) if absent
        )
        # Independently of holder grouping or the allocation oracle, holdings
        # cannot spend savings. Explicit reports may consume them as before.
        assert missing_capital >= max(0, savings - explicit_consumption) - 0.03
        missing_adults = sum(count for count, absent in zip(adults, missing) if absent)
        # This identity proves both directions: no owner's holding leaks to a
        # missing unit, and an override cannot remove that holding twice.
        for capital, count, absent in zip(row, adults, missing):
            if absent:
                assert capital == pytest.approx(
                    residual * count / missing_adults, abs=0.03
                )
        explicit_overrides = sum(spec.get("override", 0) for spec in specs)
        # Only holdings represented by corporate wealth can be conserved
        # against that pool when the person and household inputs conflict.
        assert row.sum() + sum(effective_holdings) <= pool + explicit_overrides + 0.03
        # Account for what regulation 77 actually removes from reporting
        # owners, without scaling that substitution. This identity also
        # covers inconsistent observations and exhausted residual pools.
        # A complete override is a countable figure, so the holding comes off
        # it at 90%. A recorded financial total is used unvalued, so the owner
        # loses the holding in full while the pool gives up only its 90%
        # value: what the report removes from the pool beyond the owner's own
        # remaining capital is its consumption less that capital.
        owner_substitution = sum(
            min(SHARE_VALUE * holding, reported)
            if "override" in spec
            else max(0, reported - market)
            + SHARE_VALUE * market
            - max(0, reported - holding)
            for holding, market, reported, absent, spec in zip(
                holdings, market_holdings, explicit, missing, specs
            )
            if not absent
        )
        assert row.sum() + owner_substitution + extra_holding_draw == pytest.approx(
            max(pool, explicit_consumption + extra_holding_draw), abs=0.03
        )


def _pool_property_situation(cases):
    """Batch households and retain their unreported-unit output positions."""
    people, units, households, residual_rows = {}, {}, {}, []
    for index, (specs, corporate, savings) in enumerate(cases):
        prefix = f"h{index}"
        members, missing_rows = [], []
        for unit_index, (report, adults, dependants) in enumerate(specs):
            names = []
            for role, holdings in (("adult", adults), ("child", dependants)):
                for person_index, holding in enumerate(holdings):
                    name = f"{prefix}_u{unit_index}_{role}{person_index}"
                    people[name] = _company_person(holding, dependant=role == "child")
                    names.append(name)
            unit = {"members": names, "would_claim_uc": {YEAR: True}}
            if report is None:
                missing_rows.append((len(units), len(adults)))
            else:
                unit[report] = {YEAR: 0}
            units[f"{prefix}_u{unit_index}"] = unit
            members.extend(names)
        households[prefix] = {
            "members": members,
            "savings": {YEAR: savings},
            "corporate_wealth": {YEAR: corporate},
        }
        residual_rows.append(missing_rows)
    return {
        "people": people,
        "benunits": units,
        "households": households,
    }, residual_rows


@pytest.mark.parametrize("split_route", ["override", "dependant"])
def test_increasing_or_splitting_disregarded_holdings_preserves_savings(split_route):
    """Once corporate wealth is exhausted, holdings cannot eat ordinary savings."""
    cases, comparisons = [], []
    for corporate, savings, multiplier in product(
        (0, 1_000, 4_000, 10_000), (0, 6_000, 20_000), (1, 2, 3)
    ):
        increased = corporate * multiplier
        # Keep the target and zero financial-report unit fixed while one
        # override owner's holding grows, or is split with another holder.
        arrangements = [
            [("uc_reported_capital", (corporate,), ())],
            [("uc_reported_capital", (increased,), ())],
        ]
        if split_route == "override":
            arrangements.append(
                [
                    ("uc_reported_capital", (increased * 0.6,), ()),
                    ("uc_reported_capital", (increased * 0.4,), ()),
                ]
            )
        else:
            arrangements.append(
                [("uc_reported_capital", (increased * 0.6,), (increased * 0.4,))]
            )
        start = len(cases)
        for owners in arrangements:
            cases.append(
                (
                    owners + [("benunit_reported_capital", (0,), ()), (None, (0,), ())],
                    corporate,
                    savings,
                )
            )
        comparisons.append((start, savings))
    situation, residual_rows = _pool_property_situation(cases)
    capital = np.asarray(
        Simulation(situation=situation).calculate("uc_assessable_capital", YEAR)
    )
    residual = [sum(capital[row] for row, _ in rows) for rows in residual_rows]
    for start, savings in comparisons:
        baseline, increased, split = residual[start : start + 3]
        assert baseline == pytest.approx(savings, abs=0.03)
        assert increased >= baseline - 0.03
        assert split >= increased - 0.03
        assert [increased, split] == pytest.approx([savings, savings], abs=0.03)


def test_regrouping_holdings_between_holders_and_units_preserves_residual_pool():
    """Holder counts, reporting routes and dependants share one corporate budget."""
    cases, expected = [], []
    for corporate, savings, total in product(
        (0, 1_000, 4_000, 10_000), (0, 6_000, 20_000), (0, 4_000, 10_000, 20_000)
    ):
        first, second = total * 0.6, total * 0.4
        arrangements = (
            [("uc_reported_capital", (total,), ())],
            [("uc_reported_capital", (first, second), ())],
            [
                ("uc_reported_capital", (first,), ()),
                ("uc_reported_capital", (second,), ()),
            ],
            [("uc_reported_capital", (first,), (second,))],
            [
                ("benunit_reported_capital", (0,), (first,)),
                ("benunit_reported_capital", (0,), (second,)),
            ],
            [("uc_reported_capital", (first,), ()), (None, (second,), ())],
            [(None, (first,), (second,))],
            [(None, (first,), ()), (None, (second,), ())],
        )
        for owners in arrangements:
            cases.append(
                (
                    owners + [("benunit_reported_capital", (0,), ()), (None, (0,), ())],
                    corporate,
                    savings,
                )
            )
            # Shares left after the holdings count at 90% (reg. 49(1)(a)).
            expected.append(savings + SHARE_VALUE * max(0, corporate - total))
    situation, residual_rows = _pool_property_situation(cases)
    capital = np.asarray(
        Simulation(situation=situation).calculate("uc_assessable_capital", YEAR)
    )
    residual = []
    for rows, pool in zip(residual_rows, expected):
        residual.append(sum(capital[row] for row, _ in rows))
        assert residual[-1] == pytest.approx(pool, abs=0.03)
        adults = sum(count for _, count in rows)
        for row, count in rows:
            assert capital[row] == pytest.approx(pool * count / adults, abs=0.03)
    groups = np.asarray(residual).reshape(-1, len(arrangements))
    np.testing.assert_allclose(
        groups, np.repeat(groups[:, :1], len(arrangements), axis=1), atol=0.03
    )


@pytest.mark.parametrize(
    "specs, rows, expected_capital, expected_uc",
    [
        (
            [(None, (np.inf,), ()), (None, (0,), ())],
            [0, 1],
            [10_000, 10_000],
            [4_263.60, 4_263.60],
        ),
        (
            [("benunit_reported_capital", (0,), (np.inf,)), (None, (0,), ())],
            [1],
            [20_000],
            [0],
        ),
        (
            [
                ("uc_reported_capital", (10_000,), ()),
                ("benunit_reported_capital", (-6_000,), ()),
                (None, (0,), ()),
            ],
            [0, 1, 2],
            [0, 6_000, 20_000],
            [5_098.80, 5_098.80, 0],
        ),
    ],
    ids=["infinite-owner", "infinite-dependant", "negative-offset"],
)
def test_invalid_holdings_cannot_contaminate_other_units_capital(
    specs, rows, expected_capital, expected_uc
):
    """Preserve sound parent outputs without changing raw reg. 77 substitution.

    An infinite dependant already makes its own reporting unit's raw
    substitution undefined; this regression isolates the unrelated unit.
    """
    situation, _ = _pool_property_situation([(specs, 4_000, 20_000)])
    simulation = Simulation(situation=situation)
    capital = simulation.calculate("uc_assessable_capital", YEAR)[rows]
    uc = simulation.calculate("universal_credit", YEAR)[rows]
    assert np.isfinite(capital).all()
    assert np.isfinite(uc).all()
    np.testing.assert_allclose(capital, expected_capital, atol=0.03)
    np.testing.assert_allclose(uc, expected_uc, atol=0.03)
    for variable in (
        "household_uc_reported_financial_capital",
        "household_uc_pool_company_holdings",
    ):
        assert np.isfinite(simulation.calculate(variable, YEAR)).all()


@settings(max_examples=16, deadline=None, derandomize=True)
@example(holdings=(np.inf, -np.inf, -6_000, 1e30), corporate=4_000, savings=20_000)
@example(holdings=(np.inf, 0, 0, 0), corporate=0, savings=20_000)
@given(
    holdings=st.tuples(
        *(st.floats(width=32, allow_infinity=True, allow_nan=False) for _ in range(4))
    ),
    corporate=st.floats(0, 30_000, allow_nan=False, allow_infinity=False),
    savings=st.floats(0, 50_000, allow_nan=False, allow_infinity=False),
)
def test_invalid_holdings_share_a_finite_budget_and_preserve_savings(
    holdings, corporate, savings
):
    """Invalid pool inputs cannot spend savings or poison any assessed capital.

    Non-finite holdings belong to missing-report units, including a dependant.
    Raw regulation 77 substitution for an infinite holding in a reporting unit
    is an inherited limitation outside this household-budget contract.
    """
    specs = [
        ("uc_reported_capital", (10_000,), ()),
        ("benunit_reported_capital", (-6_000,), ()),
        (None, holdings[:2], holdings[2:]),
        (None, (0,), ()),
    ]
    situation, residual_rows = _pool_property_situation([(specs, corporate, savings)])
    simulation = Simulation(situation=situation)
    capital = np.asarray(simulation.calculate("uc_assessable_capital", YEAR))
    assert np.isfinite(capital).all()
    deductions = sum(
        simulation.calculate(variable, YEAR)[0]
        for variable in (
            "household_uc_reported_financial_capital",
            "household_uc_pool_company_holdings",
        )
    )
    assert np.isfinite(deductions)
    assert 0 <= deductions <= max(0, corporate) + 0.03
    missing_capital = sum(capital[row] for row, _ in residual_rows[0])
    assert missing_capital >= savings - 0.03
