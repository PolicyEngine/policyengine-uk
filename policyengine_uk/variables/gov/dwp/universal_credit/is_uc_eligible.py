from policyengine_uk.model_api import *


class is_uc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for the Universal Credit"
    documentation = (
        "Whether a claimant or partner meets the modelled minimum-age and "
        "pension-age conditions and the benefit unit meets the capital limit. "
        "One qualifying claimant suffices, preserving mixed-age couples under "
        "regulation 3(2)(a). Dependants cannot satisfy the claimant age test, "
        "nor can a partner who cannot be a joint claimant: where a member of "
        "a couple claims as a single person (regulation 3(3)), that member "
        "must meet the conditions, and the capital tested includes the other "
        "member's (regulation 18(2)). A family on the Pension Credit route "
        "(meets_pension_credit_age_conditions) is not eligible."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/3",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/5",
    )

    def formula(benunit, period, parameters):
        capital = benunit("uc_assessable_capital", period)
        limit = parameters(period).gov.dwp.universal_credit.means_test.capital.limit
        claimant = benunit.members("is_uc_single_or_joint_claimant", period)
        meets_minimum_age = benunit.members("meets_uc_minimum_age_condition", period)
        # WRA 2012 s.4(1)(b): "has not reached the qualifying age for state
        # pension credit"; s.4(4) imports SPCA 2002 s.1(6).
        pension_age = benunit.members(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        has_qualifying_claimant = benunit.any(
            claimant & meets_minimum_age & ~pension_age
        )
        # No family gets both Pension Credit and Universal Credit (UC
        # (Transitional Provisions) Regs 2014 reg 5(1)(d)). A mixed-age couple
        # keeping the SI 2019/37 saving could still choose Universal Credit
        # jointly (UC Regs 2013 reg 3(2)(a)) and lose the saving; the model
        # keeps it on the Pension Credit route, anchored to its reported
        # Pension Credit or Housing Benefit. That, and routing mixed-age
        # couples not reported on Universal Credit to Pension Credit before
        # 15 May 2019, are modelling choices.
        pension_credit_route = benunit("meets_pension_credit_age_conditions", period)
        return has_qualifying_claimant & ~pension_credit_route & (capital <= limit)
