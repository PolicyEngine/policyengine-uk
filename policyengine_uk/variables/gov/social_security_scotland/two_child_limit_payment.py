from policyengine_uk.model_api import *


class two_child_limit_payment(Variable):
    label = "Two Child Limit Payment"
    documentation = (
        "Scotland's payment to mitigate the UK two-child benefit cap. "
        "Equals the UC child element for each child affected by the limit."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://www.gov.scot/policies/social-security/two-child-limit-payment/",
        "https://www.gov.scot/publications/draft-two-child-limit-payment-scotland-regulations-2026/",
    ]

    def formula(benunit, period, parameters):
        in_scotland = (
            benunit.household("country", period).decode_to_str() == "SCOTLAND"
        )

        # Check if payment is in effect (from December 2024)
        in_effect = parameters(
            period
        ).gov.social_security_scotland.two_child_limit_payment.in_effect

        # Get the UC child element amount for children affected by the limit
        uc_child_amount = parameters(
            period
        ).gov.dwp.universal_credit.elements.child.amount

        # Count children affected by the two-child limit
        is_child_limit_affected = benunit.members(
            "uc_is_child_limit_affected", period
        )
        affected_children = benunit.sum(is_child_limit_affected)

        # Payment equals the UC child element for each affected child
        annual_payment = affected_children * uc_child_amount * MONTHS_IN_YEAR

        return in_scotland * in_effect * annual_payment
