"""A held outside award keeps its receipt status after the ESA abolition.

Each benefit unit has a claimant with a saved award (SI 2025/1148 art. 3A(2))
and an outside adult who claims income-related ESA in their own right with
an unsaved £200 award. The family holds £5,200 of income-related ESA
(esa_income) and the claimant and partner £5,000 of it
(claimant_or_partner_esa_income), so the outside adult holds £200 in every
year. In 2027-28 the abolition has ended the outside adult's report
(esa_income_report_closed). The claimant's own 2027-28 report varies across
the three units: £5,199, £5,200 and £5,201. In the middle unit the formula
on open reports gives £5,200, the held total, from the claimant's report
alone.

own_report_is_paid applies the report closure to an outside member's status
only when both held amounts match the formula on open reports
(holds_formula_award). The held £5,000 never matches the formula's couple
part (£5,199, £5,200 or £5,201), so in every unit the outside adult stays on
income-related ESA while the benefit unit's held award stays positive.

The test holds the awards three ways: through the disable_simulated_benefits
reform ("frozen"), as entered values ("stored"), and through a reform that
replaces esa_income's formula ("replaced").
"""

import json

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.model_api import YEAR, BenUnit, Reform, Variable
from policyengine_uk.utils.scenario import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = (2025, 2026, 2027)
UNITS = ("below", "equal", "above")
CLAIMANT_REPORTS = (5_199, 5_200, 5_201)
HELD_TOTAL = 5_200
HELD_COUPLE = 5_000
OUTSIDE_REPORT = 200
FROZEN = Scenario(
    applied_before_data_load=True,
    parameter_changes={"gov.contrib.policyengine.disable_simulated_benefits": True},
)


def every_year(value):
    return {year: value for year in YEARS}


def situation(mode):
    people, benunits, households = {}, {}, {}
    for unit, claimant_report in zip(UNITS, CLAIMANT_REPORTS):
        claimant, outside = f"{unit}_claimant", f"{unit}_outside"
        for name, age, couple, reports, saved in (
            (
                claimant,
                40,
                True,
                {2025: HELD_COUPLE, 2026: HELD_COUPLE, 2027: claimant_report},
                True,
            ),
            (outside, 30, False, every_year(OUTSIDE_REPORT), False),
        ):
            people[name] = {
                "age": every_year(age),
                "is_claimant_or_partner": every_year(couple),
                "current_education": every_year("NOT_IN_EDUCATION"),
                "receives_carer_benefit": every_year(False),
                "weekly_hours": every_year(0),
                "employment_income": every_year(0),
                "esa_income_reported": reports,
                "esa_income_appointee_saving": every_year(saved),
            }
        benunits[unit] = {
            "members": [claimant, outside],
            "would_claim_uc": every_year(False),
            "would_claim_uc_at_legacy_closure": every_year(False),
            "esa_income_assessable_capital": every_year(0),
        }
        households[unit] = {
            "members": [claimant, outside],
            "region": every_year("LONDON"),
        }
        if mode != "frozen":
            # Hold what the reform holds: £5,000 for the claimant and partner,
            # and nobody moved off their legacy benefits.
            benunits[unit]["claimant_or_partner_esa_income"] = every_year(HELD_COUPLE)
            benunits[unit]["legacy_benefits_closed"] = every_year(False)
            benunits[unit]["esa_income_abolition_reached"] = every_year(False)
            for name in (claimant, outside):
                people[name]["person_legacy_benefits_closed"] = every_year(False)
            if mode == "stored":
                benunits[unit]["esa_income"] = every_year(HELD_TOTAL)
    return {"people": people, "benunits": benunits, "households": households}


class esa_income(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.filled_array(HELD_TOTAL)


class HoldTotal(Reform):
    def apply(self):
        self.update_variable(esa_income)


@pytest.mark.parametrize("mode", ("frozen", "stored", "replaced"))
def test_a_held_outside_award_survives_an_equal_formula_total(mode):
    simulation = Simulation(
        situation=situation(mode), scenario=FROZEN if mode == "frozen" else None
    )
    if mode == "replaced":
        simulation.apply_reform(HoldTotal)
    values = {
        name: simulation.calculate(name, 2027).tolist()
        for name in (
            "esa_income",
            "claimant_or_partner_esa_income",
            "person_legacy_benefits_closed",
            "esa_income_report_closed",
            "is_on_income_related_esa",
        )
    }
    print(json.dumps({"mode": mode, "values": values}, sort_keys=True))
    np.testing.assert_array_equal(values["esa_income"], [HELD_TOTAL] * 3)
    np.testing.assert_array_equal(
        values["claimant_or_partner_esa_income"], [HELD_COUPLE] * 3
    )
    np.testing.assert_array_equal(values["person_legacy_benefits_closed"], [False] * 6)
    # The abolition has ended each outside adult's unsaved report.
    np.testing.assert_array_equal(values["esa_income_report_closed"], [False, True] * 3)
    # Each outside adult has the same held award, work, capital and report;
    # only the saved claimant's 2027-28 report differs.
    assert values["is_on_income_related_esa"] == [True] * 6, (mode, values)
