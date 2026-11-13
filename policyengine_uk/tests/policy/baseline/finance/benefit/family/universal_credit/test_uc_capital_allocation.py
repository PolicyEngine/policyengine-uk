"""The financial proxy conserves residual capital after financial observations.

Each unreported unit's share of the residual is its own amount, rounded to the
nearest penny with half a penny rounded up (UC Regs 2013 reg. 6(1)), so the
shares add up to the residual to within half a penny per unit: 1.00 shared
three ways is 0.33 each.
"""

from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings, strategies as st
from policyengine_core.simulations import Simulation

from policyengine_uk.system import system


@st.composite
def household_capital_situations(draw):
    household_specs = draw(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=200_000),
                st.lists(
                    st.tuples(
                        st.integers(min_value=1, max_value=2),
                        st.integers(min_value=0, max_value=2),
                        st.booleans(),
                        st.integers(min_value=0, max_value=50_000),
                    ),
                    min_size=1,
                    max_size=4,
                ),
            ),
            min_size=1,
            max_size=3,
        )
    )
    return build_situation(household_specs)


def build_situation(household_specs):
    people, benunits, households, expected = {}, {}, {}, []
    for household_index, (capital, unit_specs) in enumerate(household_specs):
        household_members = []
        unreported_indices = []
        reported_values = {}
        for unit_index, (
            claimant_count,
            dependant_count,
            has_reported,
            reported_capital,
        ) in enumerate(unit_specs):
            # Every generated household has at least one unreported unit.
            has_reported = has_reported and unit_index > 0
            unit_id = f"household_{household_index}_unit_{unit_index}"
            members = []
            for person_index in range(claimant_count + dependant_count):
                person_id = f"{unit_id}_person_{person_index}"
                is_claimant = person_index < claimant_count
                people[person_id] = {
                    "age": {2025: 17 if is_claimant else 19},
                    "is_uc_claimant": {2025: is_claimant},
                    "is_benunit_head": {2025: person_index == 0},
                }
                members.append(person_id)
            if has_reported:
                reported_values[len(benunits)] = reported_capital
            else:
                unreported_indices.append((len(benunits), claimant_count))
            benunits[unit_id] = {
                "members": members,
                "benunit_reported_capital": {
                    2025: reported_capital if has_reported else -1
                },
            }
            household_members.extend(members)
        households[f"household_{household_index}"] = {
            "members": household_members,
            "savings": {2025: capital},
        }
        expected.append(
            (
                unreported_indices,
                reported_values,
                max(0, capital - sum(reported_values.values())),
            )
        )
    return {"people": people, "benunits": benunits, "households": households}, expected


def nearest_penny(amount):
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# Test conservation independently of machine-dependent generation timings.
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(household_capital_situations())
# 1.00 of savings shared by three single claimants is 0.33 each, 0.99 in all.
@example(build_situation([(1, [(1, 0, False, 0)] * 3)]))
def test_unreported_capital_shares_sum_to_each_households_residual(case):
    situation, expected = case
    # Reuse baseline rules; each example still gets fresh people and inputs.
    simulation = Simulation(tax_benefit_system=system, situation=situation)
    assessed_capital = simulation.calculate("uc_assessable_capital", 2025)

    assert np.isfinite(assessed_capital).all()
    for unreported_units, reported_values, residual in expected:
        claimants = sum(count for _, count in unreported_units)
        for index, count in unreported_units:
            share = Decimal(residual) * count / claimants
            assert assessed_capital[index] == pytest.approx(
                nearest_penny(share), abs=0.001
            )
        indices = [index for index, _ in unreported_units]
        assert assessed_capital[indices].sum() == pytest.approx(
            residual, abs=0.005 * len(indices) + 0.001
        )
        for index, reported_capital in reported_values.items():
            assert assessed_capital[index] == pytest.approx(reported_capital)
