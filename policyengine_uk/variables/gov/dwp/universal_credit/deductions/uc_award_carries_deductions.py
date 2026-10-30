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
        "benefit overpayments and third-party arrears. That a family a "
        "reform brings onto Universal Credit repays none of them from the "
        "new award is an assumption, and it holds in every year compared. "
        "For an advance it is a fair first-year view, since the advance is "
        "a loan paid out first; but third-party deductions (SI 2013/380 "
        "Schedule 6) and overpayment recovery apply to any claimant with "
        "those debts. So it slightly raises the cost of reforms that widen "
        "Universal Credit. A simulation is compared with its baseline only "
        "where it may differ from it (changed_from_baseline): one built "
        "with a reform, or changed after it was built by apply_reform or a "
        "step that ends with drop_computed_arrays, as policyengine.py's "
        "simulation modifiers do. Its baseline is then the current-law "
        "simulation, or the copy made when it was built. In any other "
        "simulation every award carries deductions."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/380/schedule/6"

    def formula(benunit, period, parameters):
        simulation = benunit.simulation
        baseline = getattr(simulation, "baseline", None)
        award = benunit("universal_credit_pre_benefit_cap", period) > 0
        person = benunit.members
        if (
            not getattr(simulation, "changed_from_baseline", False)
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
