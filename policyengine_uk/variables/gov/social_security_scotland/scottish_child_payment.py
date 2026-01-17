from policyengine_uk.model_api import *


class scottish_child_payment(Variable):
    label = "Scottish Child Payment"
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

        # Child-level take-up (generated stochastically in dataset)
        would_claim = person("would_claim_scp", period)

        # Convert to annual amount
        return weekly_amount * WEEKS_IN_YEAR * would_claim
