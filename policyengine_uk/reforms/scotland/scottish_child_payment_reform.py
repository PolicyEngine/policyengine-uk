from policyengine_uk.model_api import *
from policyengine_core.periods import period as period_


def create_scottish_child_payment_baby_bonus_reform() -> Reform:
    """
    Reform that implements SCP Premium for under-ones.

    Policy: Children under 1 receive a FIXED £40/week total payment.
    Children 1+ receive the standard SCP rate (inflates with inflation).

    This is NOT a fixed bonus added to the base - it's a fixed total amount.
    As the base SCP rate inflates, the "bonus" for under-1s effectively
    decreases to maintain the £40 total.

    Source: Scottish Budget 2026-27
    https://www.gov.scot/publications/scottish-budget-2026-2027-finance-secretarys-statement-13-january-2026-2/
    """

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
                benunit.household("country", period).decode_to_str()
                == "SCOTLAND"
            )

            # Get SCP parameters
            p = parameters(
                period
            ).gov.social_security_scotland.scottish_child_payment
            weekly_amount = p.amount

            # SCP only available when amount > 0 (i.e., after Feb 2021)
            scp_available = weekly_amount > 0

            # Count eligible children in the benefit unit
            is_eligible_child = benunit.members(
                "is_scp_eligible_child", period
            )
            eligible_children = benunit.sum(is_eligible_child)

            # Get ages for baby bonus calculation
            age = benunit.members("age", period)

            # Count children under 6 and 6+ for takeup rate calculation
            is_child = benunit.members("is_child", period)
            children_6_and_over = benunit.sum(
                is_child & (age >= 6) & (age < 16)
            )

            # Check if receiving a qualifying benefit
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

            # SCP Premium for under-ones: Fixed £40/week total (not base + bonus)
            # Policy: Children under 1 get £40/week, children 1+ get standard rate
            PREMIUM_RATE_UNDER_ONE = 40.0  # £40/week fixed total

            # Calculate per-child weekly amount based on age
            per_child_weekly = where(
                age < 1,
                PREMIUM_RATE_UNDER_ONE,  # £40/week for under-1s (TOTAL, not bonus)
                weekly_amount  # Standard SCP rate for 1+ (inflates with inflation)
            )

            # Calculate total weekly payment for all eligible children
            total_weekly = benunit.sum(per_child_weekly * is_eligible_child)

            # Convert to annual amount
            annual_amount = total_weekly * WEEKS_IN_YEAR

            # Apply age-specific take-up rates in microsimulation
            takeup_under_6 = p.takeup_rate.under_6
            takeup_6_and_over = p.takeup_rate.age_6_and_over

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
