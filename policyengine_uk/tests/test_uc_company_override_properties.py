"""Exhaustive MOCK company-override conservation and residual-pool properties.

A complete override describes capital before regulation 77 substitution. Its
owner's holding must leave the financial pool once: through that override,
with a floor at the holding represented by corporate wealth. Dependants own
their holdings separately. Holdings above household corporate wealth are
inconsistent proxy observations, so full conservation is asserted only for
compatible inputs; the corporate-wealth cap and residual allocation are
checked for every input, including those inconsistent observations.
"""

from itertools import product

import numpy as np
import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
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
    """Combine 960 independent three-unit households in one simulation."""
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
            (None, -1, 10_000),
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
    conserved = 0
    for row, (specs, adults, holdings, dependants, corporate, savings) in zip(
        assessed, cases
    ):
        pool = corporate + savings
        missing = [
            "override" not in spec and spec.get("financial", -1) < 0 for spec in specs
        ]
        consumed = sum(
            max(spec["override"], min(holding, corporate))
            if "override" in spec
            else max(0, spec.get("financial", -1))
            for spec, holding in zip(specs, holdings)
        )
        # Only unreported owners and dependants leave the pool separately;
        # reported claimants' holdings already belong to their report.
        uncovered = dependants + sum(
            holding for holding, absent in zip(holdings, missing) if absent
        )
        residual = max(0, pool - consumed - min(uncovered, corporate))
        missing_adults = sum(count for count, absent in zip(adults, missing) if absent)
        # This identity proves both directions: no owner's holding leaks to a
        # missing unit, and an override cannot remove that holding twice.
        for capital, count, absent in zip(row, adults, missing):
            if absent:
                assert capital == pytest.approx(
                    residual * count / missing_adults, abs=0.03
                )
        total_holdings = sum(holdings) + dependants
        explicit_overrides = sum(spec.get("override", 0) for spec in specs)
        # Only holdings represented by corporate wealth can be conserved
        # against that pool when the person and household inputs conflict.
        assert (
            row.sum() + min(sum(holdings), corporate)
            <= pool + explicit_overrides + 0.03
        )
        if total_holdings <= corporate:
            assert row.sum() + sum(holdings) <= pool + explicit_overrides + 0.03
            if consumed + uncovered <= pool:
                # At compatible observations the whole pool is accounted for,
                # including the dependant's separately disregarded holding.
                assert row.sum() + total_holdings == pytest.approx(pool, abs=0.03)
                conserved += 1
    assert conserved > 0
