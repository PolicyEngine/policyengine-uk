from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._reduction_allocation import (
    allocate_uc_reductions,
)


class uc_deductions(Variable):
    label = "UC deductions"
    documentation = (
        "Money deducted from this benefit unit's Universal Credit award to "
        "repay debts: advance repayments, government debt (benefit and tax "
        "credit overpayments) and third party deductions. Deductions leave "
        "at least one penny per assessment period payable (Schedule 6, "
        "paragraph 3(1)(a) of SI 2013/380). Per-household statistics are "
        "validated against the DWP deductions statistics; weighted "
        "aggregates are not, because they scale with the model's UC "
        "caseload, which falls short of the administrative count. "
        "Annualized from the surveyed monthly rate: for deduction types "
        "with spells shorter than a year (e.g. advance recovery), annual "
        "per-household amounts are upper bounds."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "claims_universal_credit"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.deductions
        # Shared with uc_benefit_cap_reduction_after_floor. Under current law
        # the cap reduces the award first and deductions leave a penny of
        # what is left. Where a protected minimum floor binds, deductions are met
        # first, up to the floor allowance, and the cap reduction absorbs the
        # rest. The floor also binds on last resort exceptions and maintenance
        # above the administrative cap. JRF's briefing does not say whether
        # their floor exempts those categories, so that is a modeling choice.
        deductions, _ = allocate_uc_reductions(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("uc_benefit_cap_reduction", period),
            benunit("uc_deduction_demand", period),
            benunit("uc_maximum_reduction", period),
            p.minimum_payable * MONTHS_IN_YEAR,
        )
        return deductions
