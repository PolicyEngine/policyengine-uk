from policyengine_uk.model_api import *


class is_scp_eligible_child(Variable):
    label = "Eligible for Scottish Child Payment"
    documentation = (
        "Whether this child is eligible for Scottish Child Payment based on age."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        p = parameters(period).gov.social_security_scotland.scottish_child_payment
        age = person("age", period)
        max_age = p.max_age
        return age < max_age


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
        "https://www.gov.scot/policies/social-security/scottish-child-payment/",
        "https://www.socialsecurity.gov.scot/",
    ]

    def formula(benunit, period, parameters):
        # Check if household is in Scotland
        in_scotland = (
            benunit.household("country", period).decode_to_str() == "SCOTLAND"
        )

        # Get SCP parameters
        p = parameters(period).gov.social_security_scotland.scottish_child_payment
        weekly_amount = p.amount

        # SCP only available when amount > 0 (i.e., after Feb 2021)
        scp_available = weekly_amount > 0

        # Count eligible children in the benefit unit
        is_eligible_child = benunit.members("is_scp_eligible_child", period)
        eligible_children = benunit.sum(is_eligible_child)

        # Check if receiving a qualifying benefit (UC or legacy benefits)
        # Families must be in receipt of UC, Tax Credits, or certain other benefits
        receives_uc = benunit("universal_credit", period) > 0
        receives_ctc = benunit("child_tax_credit", period) > 0
        receives_wtc = benunit("working_tax_credit", period) > 0
        receives_income_support = benunit("income_support", period) > 0
        receives_jsa_income = benunit("jsa_income", period) > 0
        receives_esa_income = benunit("esa_income", period) > 0
        receives_pension_credit = benunit("pension_credit", period) > 0

        receives_qualifying_benefit = (
            receives_uc
            | receives_ctc
            | receives_wtc
            | receives_income_support
            | receives_jsa_income
            | receives_esa_income
            | receives_pension_credit
        )

        # Calculate annual payment
        annual_amount = eligible_children * weekly_amount * WEEKS_IN_YEAR

        # Apply take-up rate in microsimulation
        takeup_rate = p.takeup_rate
        takes_up = random(benunit) < takeup_rate
        is_in_microsimulation = benunit.simulation.dataset is not None
        if is_in_microsimulation:
            receives_payment = takes_up
        else:
            receives_payment = True

        return (
            in_scotland
            * scp_available
            * receives_qualifying_benefit
            * receives_payment
            * annual_amount
        )
