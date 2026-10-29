from policyengine_uk.model_api import *
from policyengine_uk.utils.household_subset import household_subset


class uc_award_carries_deductions(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit award carries debt deductions"
    documentation = (
        "Whether debt deductions can come out of this family's Universal "
        "Credit award: true unless the family has an award here but none "
        "in the simulation's baseline. The deduction incidence, rates and "
        "types describe the existing caseload's debts, such as advances, "
        "benefit overpayments and third-party arrears. A family a reform "
        "brings onto Universal Credit has no such debt to repay from the "
        "new award; an advance on a new claim is a loan paid out first. "
        "Only a simulation built with a reform is compared with its "
        "baseline, the current-law simulation. In one built without, every "
        "award carries deductions: its baseline is a copy of itself, so "
        "the comparison could only miss changes made after it was built, "
        "such as a simulation modifier, and would cost a second "
        "Universal Credit calculation."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        simulation = benunit.simulation
        baseline = getattr(simulation, "baseline", None)
        award = benunit("universal_credit_pre_benefit_cap", period) > 0
        person = benunit.members
        if (
            not getattr(simulation, "built_with_reform", False)
            or baseline is None
            or not award.any()
            or baseline.populations["person"].count != person.count
        ):
            return np.ones(benunit.count, dtype=bool)
        # Only an award here can lose its deductions, so the baseline award
        # is worked out for the households holding one, in a branch holding
        # only them.
        with household_subset(
            baseline, "uc_award_in_baseline", benunit.project(award)
        ) as households:
            in_baseline = households.expand(
                households.simulation.populations["person"].benunit(
                    "universal_credit_pre_benefit_cap", period
                )
                > 0
            )
        return ~award | benunit.any(in_baseline)
