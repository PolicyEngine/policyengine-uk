from policyengine_uk.model_api import *
from policyengine_core.periods import period as period_


def create_scottish_child_payment_baby_bonus_reform() -> Reform:
    """
    Reform that implements SCP baby bonus for children under 1.

    Policy: Children under 1 receive a total of £40/week (the policy parameter).
    The "bonus" is implicitly the difference between this total and the base rate.

    Source: Scottish Budget 2026-27
    https://www.gov.scot/publications/scottish-budget-2026-2027/pages/6/
    "This will bring the total Scottish Child Payment amount to £40 a week
    for children under 1."
    """

    class scottish_child_payment(Variable):
        label = "Scottish Child Payment"
        documentation = (
            "Scottish Child Payment amount for this child. "
            "Paid to eligible children in families receiving qualifying benefits. "
            "When baby bonus reform is active, children under 1 receive £40/week total."
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
            # Get base SCP rate
            p = parameters(
                period
            ).gov.social_security_scotland.scottish_child_payment
            base_weekly = p.amount

            # Get reform parameters
            scp_reform = parameters(
                period
            ).gov.contrib.scotland.scottish_child_payment
            in_effect = scp_reform.in_effect
            under_one = scp_reform.under_one

            # For under-1s when reform in effect: use under_one total
            # Otherwise: use base rate
            age = person("age", period)
            weekly_amount = where(
                (age < 1) & in_effect,
                under_one,
                base_weekly,
            )

            # Child-level take-up (generated stochastically in dataset)
            would_claim = person("would_claim_scp", period)

            # Convert to annual amount
            return weekly_amount * WEEKS_IN_YEAR * would_claim

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
