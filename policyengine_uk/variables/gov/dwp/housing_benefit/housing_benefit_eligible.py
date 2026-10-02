from policyengine_uk.model_api import *


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligible for the Housing Benefit"
    documentation = (
        "Whether this family can receive Housing Benefit. A family in which "
        "every adult has reached the qualifying age for State Pension Credit "
        "can make a new claim; Universal Credit is not available to it. "
        "in_specified_or_temporary_accommodation also opens the new-claim "
        "route at any age, including alongside Universal Credit, and "
        "preserves existing awards. Other families keep Housing Benefit "
        "only while they continue an "
        "existing award (reported Housing Benefit) and do not claim "
        "Universal Credit. Unprotected working-age awards ended on 1 July 2026 in Great "
        "Britain and 1 October 2026 in Northern Ireland, so from then only "
        "families with a member over State Pension age or the accommodation "
        "input continue one. Other unmodelled statutory savings are listed "
        "in housing_benefit_payable_share's documentation. Rental, capital "
        "and take-up rules still apply; accommodation-specific eligible rent "
        "and benefit-cap rules are not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/4A",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        sp_age = person("is_SP_age", period)
        # Apart from the accommodation exception, new claims are barred
        # except where the claimant, and any partner,
        # has reached the qualifying age for State Pension Credit
        # (SI 2014/1230 reg 6A(4); NI: SR 2016/226 reg 4A(4)). The current HB
        # approximation counts members aged 18 or over, so an 18 or 19 year
        # old dependant prevents this pension-age route.
        adult = person("age", period) >= 18
        adult_count = benunit.sum(adult)
        pension_age = (adult_count > 0) & (benunit.sum(adult & sp_age) == adult_count)
        # Working-age and mixed-age families (since 15 May 2019) claim
        # Universal Credit instead. They keep an existing award until they
        # claim it (reg 8(2A)), so this route also rules out receiving
        # Universal Credit. For mixed-age couples the reported award stands
        # in for the SI 2019/37 art. 4 saving (reg 6A(5)). Working-age awards
        # outside specified or temporary accommodation were abolished from
        # 1 July 2026 in Great Britain (SI 2025/1148 art. 7) and 1 October
        # 2026 in Northern Ireland (SR 2025/176 art. 7); a family with no
        # member over State Pension age continues one only for the part of
        # the year before that date (housing_benefit_payable_share).
        already_claiming = add(benunit, period, ["housing_benefit_reported"]) > 0
        claiming_uc = benunit("would_claim_uc", period)
        still_payable = benunit("housing_benefit_payable_share", period) > 0
        continuing_award = already_claiming & ~claiming_uc & still_payable
        # Reg 6A(2) permits new accommodation claims irrespective of UC;
        # reg 8(3) preserves accommodation HB when UC is claimed.
        # NI equivalents: SR 2016/226 regs 4A(2) and 6(3).
        protected_accommodation = benunit(
            "in_specified_or_temporary_accommodation", period
        )
        social = benunit.any(person("in_social_housing", period))
        lha_eligible = benunit("LHA_eligible", period)
        any_over_SP_age = benunit.any(sp_age)
        capital = benunit("housing_benefit_assessable_capital", period)
        hb_capital = parameters(period).gov.dwp.housing_benefit.means_test.capital
        limit = where(
            any_over_SP_age,
            hb_capital.pension_age.limit,
            hb_capital.working_age.limit,
        )
        return (
            (pension_age | continuing_award | protected_accommodation)
            & (social | lha_eligible)
            & (capital <= limit)
        )
