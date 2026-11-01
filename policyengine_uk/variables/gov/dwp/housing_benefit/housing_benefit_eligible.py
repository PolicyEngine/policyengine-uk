from policyengine_uk.model_api import *


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligible for the Housing Benefit"
    documentation = (
        "Whether this family can receive Housing Benefit. A family whose "
        "claimant and any partner have reached the qualifying age for State "
        "Pension Credit can make a new claim, unless DWP moved it to "
        "Universal Credit when its legacy benefits closed and it claimed and "
        "is entitled before benefit-cap reductions and deductions "
        "(left_pension_route_at_legacy_closure). SI 2014/1230 reg 60A "
        "disapplies the Universal Credit upper age condition for that claim "
        "if, when the migration notice was issued, the claimant, or each "
        "joint claimant, was entitled to Working Tax Credit and not to "
        "Pension Credit; the model reads reported Working Tax Credit and "
        "Pension Credit. Any "
        "other family keeps Housing Benefit only while it continues an "
        "existing award (reported Housing Benefit) and does not claim "
        "Universal Credit. DWP's move off a closed legacy benefit "
        "(legacy_benefits_closed) also ends that award, unless the family "
        "lives in specified or temporary accommodation "
        "(in_specified_or_temporary_accommodation): SI 2014/1230 reg 46(2) "
        "(NI: SR 2016/226 reg 47(2)) keeps such an award when the migration "
        "notice's deadline passes without a claim, whichever legacy benefit "
        "closed. The model leaves out new claims for that accommodation (reg "
        "6A(2)) and reg 8(3), which keeps such an award after a Universal "
        "Credit claim: the model's Universal Credit pays a housing costs "
        "element for these homes, so Housing Benefit beside it would pay the "
        "rent twice. SI 2025/1148 art. 7 ends every other working-age award "
        "on 1 July 2026 without a claim (SR 2025/176 art. 7: 1 October 2026 "
        "in Northern Ireland). The model doesn't apply that date yet, so it "
        "pays such an award for the whole of 2026-27 and keeps it until the "
        "family claims or DWP moves it; #1910 adds the date."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/4",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60A",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/4A",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/47",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # New claims are barred except where the claimant, and any partner,
        # has reached the qualifying age for State Pension Credit
        # (SI 2014/1230 reg 6A(4); NI: SR 2016/226 reg 4A(4)), or the claim
        # is made by the older member of a mixed-age couple that keeps the
        # SI 2019/37 art. 4 saving (reg 6A(5); NI reg 4A(5)). Before 15 May
        # 2019 mixed-age couples could claim too. These are the Pension
        # Credit age conditions. In the model they rule out Universal Credit
        # (is_uc_eligible) except for a family that claims it when DWP moves
        # it off its legacy benefits: a mixed-age couple claiming jointly
        # (UC Regs 2013 reg 3(2)(a)), or a pension-age claimant, or joint
        # claimants, on Working Tax Credit and not Pension Credit, for whom
        # SI 2014/1230 reg 60A disapplies the upper age condition. Such a
        # family leaves this route once it is entitled (below), so no family
        # on this route receives Universal Credit. The conditions read the
        # claimant and partner (is_claimant_or_partner), so a pensioner's 18
        # or 19 year old dependant neither takes the family off this route
        # nor makes it eligible for Universal Credit.
        # A family DWP moved to Universal Credit leaves this route if it
        # claims Universal Credit and is entitled before benefit-cap reductions
        # and deductions (left_pension_route_at_legacy_closure). One that does
        # not claim, or claims with nil entitlement, keeps it; a protected
        # mixed-age couple can reclaim Housing Benefit and keep its saving
        # (SI 2019/37 art. 4(3)(b)(ii), inserted by SI 2024/604 art. 2).
        pension_age = benunit("meets_pension_credit_age_conditions", period) & ~benunit(
            "left_pension_route_at_legacy_closure", period
        )
        # Working-age families, and mixed-age couples without the saving
        # (since 15 May 2019), claim Universal Credit instead. They keep an
        # existing award until they claim it (reg 8(2A)), so this route also
        # rules out receiving Universal Credit. SI 2025/1148 art. 7 ends the
        # remaining working-age awards on 1 July 2026 without a claim (SR
        # 2025/176 art. 7: 1 October 2026 in Northern Ireland), except in
        # specified or temporary accommodation (art. 7(4)(a), through reg
        # 6A(2); NI reg 4A(2)). The model doesn't apply that date yet, so it
        # pays such an award for the whole of 2026-27 and keeps it until the
        # family claims or DWP moves it; #1910 adds the date.
        already_claiming = add(benunit, period, ["housing_benefit_reported"]) > 0
        claiming_uc = benunit("claims_universal_credit", period)
        # Once another of the family's legacy benefits has closed, DWP's
        # migration notice ends this award even if the family does not claim
        # Universal Credit (reg 46(1)(a)), but not an award for specified or
        # temporary accommodation, whichever legacy benefit closed (reg
        # 46(2); NI: SR 2016/226 reg 47(2)). A claim still ends that award
        # here: reg 8(3) keeps it, but the model's Universal Credit pays a
        # housing costs element for these homes, so keeping it would pay the
        # rent twice.
        migrated = benunit("legacy_benefits_closed", period)
        accommodation = benunit("in_specified_or_temporary_accommodation", period)
        continuing_award = already_claiming & ~claiming_uc & (~migrated | accommodation)
        social = benunit.any(person("in_social_housing", period))
        lha_eligible = benunit("LHA_eligible", period)
        pension_age_regulations = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )
        capital = benunit("housing_benefit_assessable_capital", period)
        hb_capital = parameters(period).gov.dwp.housing_benefit.means_test.capital
        limit = where(
            pension_age_regulations,
            hb_capital.pension_age.limit,
            hb_capital.working_age.limit,
        )
        return (
            (pension_age | continuing_award)
            & (social | lha_eligible)
            & (capital <= limit)
        )
