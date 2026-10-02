from policyengine_uk.model_api import *


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligible for the Housing Benefit"
    documentation = (
        "Whether this family can receive Housing Benefit. A family whose "
        "claimant and any partner have reached the qualifying age for State "
        "Pension Credit "
        "can make a new claim; Universal Credit is not available to it. Any "
        "other family keeps Housing Benefit only while it continues an "
        "existing award (reported Housing Benefit) and does not claim "
        "Universal Credit. Claims for specified or temporary accommodation "
        "are not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/4A",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        sp_age = person("is_SP_age", period)
        # New claims are barred except where the claimant, and any partner,
        # has reached the qualifying age for State Pension Credit
        # (SI 2014/1230 reg 6A(4); NI: SR 2016/226 reg 4A(4)). This is the
        # same claimant-and-partner set is_uc_eligible and
        # is_pension_credit_eligible use, so a pensioner with an 18 or 19 year
        # old dependant can claim Housing Benefit and not Universal Credit;
        # change the three together.
        claimant_or_partner = person("is_claimant_or_partner", period)
        count = benunit.sum(claimant_or_partner)
        pension_age = (count > 0) & (benunit.sum(claimant_or_partner & sp_age) == count)
        # Working-age and mixed-age families (since 15 May 2019) claim
        # Universal Credit instead. They keep an existing award until they
        # claim it (reg 8(2A)), so this route also rules out receiving
        # Universal Credit. For mixed-age couples the reported award stands
        # in for the SI 2019/37 art. 4 saving (reg 6A(5)). Working-age awards
        # outside specified or temporary accommodation ended on 1 July 2026
        # in Great Britain (SI 2025/1148 art. 7); that is not modelled.
        already_claiming = add(benunit, period, ["housing_benefit_reported"]) > 0
        claiming_uc = benunit("would_claim_uc", period)
        continuing_award = already_claiming & ~claiming_uc
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
            (pension_age | continuing_award)
            & (social | lha_eligible)
            & (capital <= limit)
        )
