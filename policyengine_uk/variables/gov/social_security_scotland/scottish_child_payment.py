from policyengine_uk.model_api import *


class scottish_child_payment_person(Variable):
    label = "Scottish Child Payment (per child)"
    documentation = (
        "Scottish Child Payment amount for this child. "
        "Paid to eligible children in families receiving qualifying benefits."
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

        # Get age for baby bonus calculation
        age = person("age", period)

        # SCP Premium for under-ones (Scottish Budget 2026-27)
        premium_rate = p.premium_under_one_amount

        # Calculate weekly amount based on age
        weekly = where(
            (age < 1) & (premium_rate > 0),
            premium_rate,  # Premium for under-1s (TOTAL amount, not bonus)
            weekly_amount,  # Standard SCP rate
        )

        # Child-level take-up (generated stochastically in dataset)
        would_claim = person("would_claim_scp", period)

        # Convert to annual amount
        return weekly * WEEKS_IN_YEAR * would_claim


class scottish_child_payment(Variable):
    label = "Scottish Child Payment"
    documentation = (
        "Scottish Child Payment provides financial support to low-income "
        "families in Scotland. It is paid per eligible child to families "
        "receiving qualifying benefits such as Universal Credit."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ssi/2020/351/contents",
        "https://www.gov.scot/policies/social-security/scottish-child-payment/",
    ]

    adds = ["scottish_child_payment_person"]
