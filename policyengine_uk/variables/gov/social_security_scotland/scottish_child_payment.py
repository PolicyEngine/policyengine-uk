from policyengine_uk.model_api import *


class scottish_child_payment(Variable):
    label = "Scottish Child Payment"
    documentation = (
        "Scottish Child Payment provides financial support to low-income "
        "families in Scotland. It is paid per eligible child to families "
        "receiving qualifying benefits such as Universal Credit."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["benunit"]
    defined_for = "would_claim_scp"
    reference = [
        "https://www.legislation.gov.uk/ssi/2020/351/contents",
        "https://www.gov.scot/policies/social-security/scottish-child-payment/",
    ]

    def formula(person, period, parameters):
        # Check if household is in Scotland
        in_scotland = (
            person.household("country", period).decode_to_str() == "SCOTLAND"
        )

        # Get SCP parameters
        p = parameters(
            period
        ).gov.social_security_scotland.scottish_child_payment
        weekly_amount = p.amount

        # SCP only available when amount > 0 (i.e., after Feb 2021)
        scp_available = weekly_amount > 0

        # Check if child is eligible
        is_eligible_child = person("is_scp_eligible_child", period)

        # Get age for baby bonus calculation
        age = person("age", period)

        # Check if family receives a qualifying benefit
        qb = p.qualifying_benefits
        benunit = person.benunit

        receives_uc = (
            benunit("universal_credit", period) > 0
        ) & qb.universal_credit
        receives_ctc = (
            benunit("child_tax_credit", period) > 0
        ) & qb.child_tax_credit
        receives_wtc = (
            benunit("working_tax_credit", period) > 0
        ) & qb.working_tax_credit
        receives_income_support = (
            benunit("income_support", period) > 0
        ) & qb.income_support
        receives_jsa_income = (
            benunit("jsa_income", period) > 0
        ) & qb.jsa_income
        receives_esa_income = (
            benunit("esa_income", period) > 0
        ) & qb.esa_income
        receives_pension_credit = (
            benunit("pension_credit", period) > 0
        ) & qb.pension_credit

        receives_qualifying_benefit = (
            receives_uc
            | receives_ctc
            | receives_wtc
            | receives_income_support
            | receives_jsa_income
            | receives_esa_income
            | receives_pension_credit
        )

        # SCP Premium for under-ones (Scottish Budget 2026-27)
        # Children under 1 receive £40/week total from April 2026
        premium_rate = p.premium_under_one_amount

        # Calculate weekly amount based on age
        weekly = where(
            (age < 1) & (premium_rate > 0),
            premium_rate,  # Premium for under-1s (TOTAL amount, not bonus)
            weekly_amount,  # Standard SCP rate
        )

        # Convert to annual amount
        annual_amount = weekly * WEEKS_IN_YEAR

        return (
            in_scotland
            * scp_available
            * is_eligible_child
            * receives_qualifying_benefit
            * annual_amount
        )
