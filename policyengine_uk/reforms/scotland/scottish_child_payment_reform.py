from policyengine_uk.model_api import *
from policyengine_core.periods import period as period_


def create_scottish_child_payment_baby_bonus_reform() -> Reform:
    """
    Reform that implements SCP baby bonus for children under 1.

    Policy: Children under 1 receive an additional weekly bonus on top of
    the standard SCP rate. The bonus amount is parameterized at
    gov.contrib.scotland.scottish_child_payment.baby_bonus.

    Source: Scottish Budget 2026-27
    https://www.gov.scot/publications/scottish-budget-2026-2027-finance-secretarys-statement-13-january-2026-2/
    """

    class scottish_child_payment(Variable):
        label = "Scottish Child Payment"
        documentation = (
            "Scottish Child Payment amount for this child. "
            "Paid to eligible children in families receiving qualifying benefits. "
            "When baby bonus reform is active, children under 1 receive additional payment."
        )
        entity = Person
        definition_period = YEAR
        value_type = float
        unit = GBP
        defined_for = "is_scp_eligible"
        reference = [
            "https://www.legislation.gov.uk/ssi/2020/351/contents",
            "https://www.gov.scot/policies/social-security/scottish-child-payment/",
        ]

        def formula(person, period, parameters):
            # Get SCP parameters
            p = parameters(
                period
            ).gov.social_security_scotland.scottish_child_payment
            weekly_amount = p.amount

            # Get baby bonus parameter (age-bracketed)
            baby_bonus_params = parameters(
                period
            ).gov.contrib.scotland.scottish_child_payment.baby_bonus
            age = person("age", period)
            baby_bonus = baby_bonus_params.calc(age)

            # Total weekly amount = base + baby bonus
            total_weekly = weekly_amount + baby_bonus

            # Child-level take-up (generated stochastically in dataset)
            would_claim = person("would_claim_scp", period)

            # Convert to annual amount
            return total_weekly * WEEKS_IN_YEAR * would_claim

    class reform(Reform):
        def apply(self):
            self.update_variable(scottish_child_payment)

    return reform


def create_scottish_child_payment_reform(
    parameters, period, bypass: bool = False
):
    if bypass:
        return create_scottish_child_payment_baby_bonus_reform()

    p = parameters.gov.contrib.scotland.scottish_child_payment

    # Check if reform is active in current period or next 5 years
    reform_active = False
    current_period = period_(period)

    for i in range(5):
        if p(current_period).in_effect:
            reform_active = True
            break
        current_period = current_period.offset(1, "year")

    if reform_active:
        return create_scottish_child_payment_baby_bonus_reform()
    else:
        return None


scottish_child_payment_reform = (
    create_scottish_child_payment_baby_bonus_reform()
)
