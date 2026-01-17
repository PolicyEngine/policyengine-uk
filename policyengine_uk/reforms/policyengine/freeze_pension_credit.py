from policyengine_core.model_api import *
from policyengine_uk.model_api import BenUnit, YEAR, GBP


def create_freeze_pension_credit() -> Reform:
    """
    Reform that freezes Pension Credit payments to their baseline values.

    Policy: When active, Pension Credit payments are set to whatever they
    would be under baseline policy, effectively freezing the benefit.
    """

    class pension_credit(Variable):
        label = "Pension Credit"
        entity = BenUnit
        definition_period = YEAR
        value_type = float
        unit = GBP
        reference = "https://www.legislation.gov.uk/ukpga/2002/16/contents"

        def formula(benunit, period, parameters):
            # When freeze is active, return baseline value
            baseline = benunit.simulation.baseline
            if baseline is not None:
                return baseline.populations["benunit"](
                    "pension_credit", period
                )
            # Fallback to standard calculation if no baseline
            entitlement = benunit("pension_credit_entitlement", period)
            would_claim = benunit("would_claim_pc", period)
            return entitlement * would_claim

    class reform(Reform):
        def apply(self):
            self.update_variable(pension_credit)

    return reform


def create_freeze_pension_credit_reform(
    parameters, period, bypass: bool = False
):
    if bypass:
        return create_freeze_pension_credit()

    if parameters(period).gov.contrib.freeze_pension_credit:
        return create_freeze_pension_credit()
    else:
        return None


# For direct import
freeze_pension_credit_reform = create_freeze_pension_credit()
