from openfisca_uk.model_api import *
from openfisca_uk.tools.variables import variables


def apply_takeup_rates() -> Type[Reform]:
    """Creates a Reform object applying benefit takeup rates to means-tested benefits.

    Returns:
        Type[Reform]: The OpenFisca reform.
    """

    class would_claim_CTC(variables.would_claim_CTC):
        def formula(benunit, period, parameters):
            return (
                random(benunit)
                < parameters(
                    period
                ).benefit.tax_credits.child_tax_credit.takeup
            )

    class would_claim_WTC(variables.would_claim_WTC):
        def formula(benunit, period, parameters):
            return (
                random(benunit)
                < parameters(
                    period
                ).benefit.tax_credits.working_tax_credit.takeup
            )

    class would_claim_HB(variables.would_claim_HB):
        def formula(benunit, period, parameters):
            return (
                random(benunit)
                < parameters(period).benefit.housing_benefit.takeup
            )

    class would_claim_IS(variables.would_claim_IS):
        def formula(benunit, period, parameters):
            return (
                random(benunit)
                < parameters(period).benefit.income_support.takeup
            )

    class would_claim_PC(variables.would_claim_PC):
        def formula(benunit, period, parameters):
            return (
                random(benunit)
                < parameters(period).benefit.pension_credit.takeup
            )

    class claims_legacy_benefits(variables.claims_legacy_benefits):
        def formula(benunit, period, parameters):
            # Assign legacy/UC claimant status, consistently for each household
            household = benunit.members.household
            benunit_random = benunit.value_from_first_person(
                household.project(random(household))
            )
            UC_rollout = parameters(
                period
            ).benefit.universal_credit.rollout_rate
            return benunit_random > UC_rollout

    class takeup_rates(Reform):
        def apply(self):
            self.update_variable(would_claim_CTC)
            self.update_variable(would_claim_WTC)
            self.update_variable(would_claim_HB)
            self.update_variable(would_claim_IS)
            self.update_variable(would_claim_PC)
            self.update_variable(claims_legacy_benefits)

    return takeup_rates
