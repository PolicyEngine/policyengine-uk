from policyengine_uk.model_api import *


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligible for the Housing Benefit"
    documentation = (
        "Whether this family can receive Housing Benefit. A family whose "
        "claimant and any partner have reached the qualifying age for State "
        "Pension Credit can make a new claim; it claims Universal Credit only "
        "if DWP moved it there from Working Tax Credit "
        "(left_pension_route_at_legacy_closure). "
        "in_specified_or_temporary_accommodation also opens "
        "the new-claim route at any age, including alongside Universal Credit, "
        "and preserves existing awards. Other families keep Housing Benefit "
        "only while they continue an existing award (reported Housing "
        "Benefit), do not claim Universal Credit and have not been moved off "
        "a closed legacy benefit (legacy_benefits_closed). Unprotected working-age "
        "awards ended on 1 July 2026 in Great Britain and 1 October 2026 in "
        "Northern Ireland, so from then only families meeting the Pension "
        "Credit age conditions or with the accommodation input continue one. "
        "Other unmodelled "
        "statutory savings are listed in housing_benefit_payable_share's "
        "documentation. Rental, capital and take-up rules still apply; "
        "accommodation-specific eligible rent and benefit-cap rules are not "
        "modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/4",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/4A",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # Apart from the accommodation exception, new claims are barred
        # except where the claimant, and any partner,
        # has reached the qualifying age for State Pension Credit
        # (SI 2014/1230 reg 6A(4); NI: SR 2016/226 reg 4A(4)), or the claim
        # is made by the older member of a mixed-age couple that keeps the
        # SI 2019/37 art. 4 saving (reg 6A(5); NI reg 4A(5)). Before 15 May
        # 2019 mixed-age couples could claim too. These are the Pension
        # Credit age conditions, which also rule out Universal Credit
        # (is_uc_eligible), so no family on this route receives it. They read
        # the claimant and partner (is_claimant_or_partner), so a pensioner
        # with an 18 or 19 year old dependant can claim Housing Benefit and
        # not Universal Credit.
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
        # rules out receiving Universal Credit. Working-age awards outside
        # specified or temporary accommodation were abolished from 1 July
        # 2026 in Great Britain (SI 2025/1148 art. 7) and 1 October 2026 in
        # Northern Ireland (SR 2025/176 art. 7); a family outside the reg
        # 6A(2)-(5) savings continues one only for the part of the year
        # before that date (housing_benefit_payable_share).
        already_claiming = add(benunit, period, ["housing_benefit_reported"]) > 0
        claiming_uc = benunit("claims_universal_credit", period)
        # Once another of the family's legacy benefits has closed, DWP's
        # migration notice ends this award even if the family does not claim
        # Universal Credit (reg 46(1)(a), (2)).
        migrated = benunit("legacy_benefits_closed", period)
        still_payable = benunit("housing_benefit_payable_share", period) > 0
        continuing_award = already_claiming & ~claiming_uc & ~migrated & still_payable
        # Reg 6A(2) permits new accommodation claims irrespective of UC;
        # reg 8(3) preserves accommodation HB when UC is claimed.
        # NI equivalents: SR 2016/226 regs 4A(2) and 6(3).
        protected_accommodation = benunit(
            "in_specified_or_temporary_accommodation", period
        )
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
            (pension_age | continuing_award | protected_accommodation)
            & (social | lha_eligible)
            & (capital <= limit)
        )
