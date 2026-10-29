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
        "(meets_pension_credit_age_conditions) is not eligible unless it "
        "claims when DWP moves it off its legacy benefits "
        "(claims_uc_at_legacy_closure)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/3",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60A",
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
        # jointly (UC Regs 2013 reg 3(2)(a)) and leave the saving while entitled;
        # the model
        # keeps it on the Pension Credit route, anchored to its reported
        # Pension Credit or Housing Benefit. That, and routing mixed-age
        # couples not reported on Universal Credit to Pension Credit before
        # 15 May 2019, are modelling choices.
        pension_credit_route = benunit("meets_pension_credit_age_conditions", period)
        # A family DWP moved off its legacy benefits claims Universal Credit
        # even from the pension-age route: a protected mixed-age couple
        # claims jointly (reg 3(2)(a)), leaving the pension-age route only
        # while entitled, and a pension-age Working Tax Credit recipient has
        # the upper age condition waived (SI 2014/1230 reg 60A). Reg 60A(1)
        # waives it for a qualifying claim if, when the migration notice is
        # issued, the single claimant, or each joint claimant, has reached
        # the qualifying age for State Pension Credit, is entitled to an
        # award of Working Tax Credit and is not entitled to an award of
        # State Pension Credit. The model reads the year's reported receipt
        # instead. legacy_award_is_closed never closes the legacy awards of a
        # family whose claimant or partner reports Pension Credit
        # (pension_credit_reported), so legacy_benefits_closed is false and it
        # makes no closure claim. reg_60a reads reported Working Tax Credit,
        # so a family whose Working Tax Credit tapered to nil, which reg
        # 60A(2) also covers, is not modelled as a reg 60A migrant.
        # Any other pension-age Working Tax Credit recipient can make the
        # reg 60A claim, whether or not it would claim Pension Credit in the
        # model (would_claim_pc). Except in prescribed cases, no one is
        # entitled to State Pension Credit without making, or being treated
        # as making, a claim (SSAA 1992 s.1(1) and (4)(ab)), so for a family
        # that has not claimed it this matches the regulation. Where the
        # report and the award differ, it does not: a family with an award it
        # does not report is treated as a reg 60A migrant, where the
        # regulation refuses the waiver, and one reporting Pension Credit it
        # is not awarded makes no closure claim.
        closure_claim = benunit("claims_uc_at_legacy_closure", period)
        on_working_tax_credit = (
            add(benunit, period, ["working_tax_credit_reported"]) > 0
        )
        reg_60a = on_working_tax_credit & benunit.any(claimant & meets_minimum_age)
        route = (has_qualifying_claimant & ~pension_credit_route) | (
            closure_claim & (has_qualifying_claimant | reg_60a)
        )
        return route & (capital <= limit)
