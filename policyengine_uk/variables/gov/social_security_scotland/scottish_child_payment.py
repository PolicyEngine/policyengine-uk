from policyengine_uk.model_api import *


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
        p = parameters(
            period
        ).gov.social_security_scotland.scottish_child_payment
        weekly_amount = p.amount

        # SCP only available when amount > 0 (i.e., after Feb 2021)
        scp_available = weekly_amount > 0

        # Count eligible children in the benefit unit
        is_eligible_child = benunit.members("is_scp_eligible_child", period)

        # Get ages for baby bonus calculation
        age = benunit.members("age", period)
        is_child = benunit.members("is_child", period)
        children_6_and_over = benunit.sum(is_child & (age >= 6) & (age < 16))

        # Check if receiving a qualifying benefit
        # The list of qualifying benefits is parameterized as CTC/WTC
        # were removed in 2024 as part of UC migration
        qb = p.qualifying_benefits

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

        # Check if SCP Premium for under-ones is enabled
        # Scottish Budget 2026-27: £40/week for children under 1
        contrib_params = parameters(
            period
        ).gov.contrib.scotland.scottish_child_payment
        baby_bonus_in_effect = contrib_params.in_effect

        # Get the premium rate from parameters (£40/week from April 2026)
        premium_rate = p.premium_under_one_amount

        # Calculate per-child weekly amount based on age
        # Under-1s get premium rate when in effect, others get standard rate
        per_child_weekly = where(
            baby_bonus_in_effect & (age < 1) & (premium_rate > 0),
            premium_rate,  # Premium for under-1s (TOTAL amount, not bonus)
            weekly_amount,  # Standard SCP rate for 1+ or when premium not in effect
        )

        # Calculate total weekly payment for all eligible children
        total_weekly = benunit.sum(per_child_weekly * is_eligible_child)

        # Convert to annual amount
        annual_amount = total_weekly * WEEKS_IN_YEAR

        # Apply age-specific take-up rates in microsimulation
        # 97% for families with only children under 6
        # 86% for families with any children 6 and over
        takeup_under_6 = p.takeup_rate.under_6
        takeup_6_and_over = p.takeup_rate.age_6_and_over

        # Use the 6+ rate if any child is 6 or older, otherwise under-6 rate
        has_children_6_and_over = children_6_and_over > 0
        takeup_rate = where(
            has_children_6_and_over, takeup_6_and_over, takeup_under_6
        )

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
