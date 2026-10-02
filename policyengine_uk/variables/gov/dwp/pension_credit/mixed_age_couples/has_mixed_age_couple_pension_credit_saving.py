from policyengine_uk.model_api import *


class has_mixed_age_couple_pension_credit_saving(Variable):
    value_type = bool
    entity = BenUnit
    label = "Mixed-age couple keeps Pension Credit under the SI 2019/37 saving"
    documentation = (
        "Whether the State Pension Credit Act 2002 s.4(1A) exclusion does not "
        "apply to a mixed-age couple, because on 14 May 2019 the couple was "
        "entitled, as that couple, to Pension Credit or pension-age Housing "
        "Benefit, and has been entitled to one of them ever since. Set it as "
        "an input where it is known. By default it is inferred from current "
        "receipt: reported Pension Credit, or Housing Benefit reported by the "
        "pension-age member without Income Support, income-based JSA or "
        "income-related ESA (which would "
        "put the couple under the working-age Housing Benefit Regulations), "
        "with no reported Universal Credit, where the older member was born "
        "early enough to have reached the qualifying age by 14 May 2019."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2019/37/article/2",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/5",
        "https://www.legislation.gov.uk/nisr/2019/4/article/4",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.mixed_age_couples

        person = benunit.members
        # Only the claimant and partner's own awards and ages count: the
        # saving belongs to the couple (art. 4(1)), not to other members of
        # the benefit unit.
        claimant_or_partner = person("is_claimant_or_partner", period)

        def reported(variables):
            amount = sum(person(variable, period) for variable in variables)
            return benunit.sum(amount * claimant_or_partner) > 0

        # Art. 2(3): only Housing Benefit under the pension-age regulations
        # (SI 2006/214) carries the saving. They apply to a claimant who has
        # reached the qualifying age (reg 5(1)), so only HB reported by the
        # pension-age member counts, and not where the couple is on an
        # income-related legacy benefit, which puts it under the working-age
        # regulations (reg 5(2)).
        pension_age_member_hb = (
            benunit.sum(
                person("housing_benefit_reported", period)
                * person("is_SP_age", period)
                * claimant_or_partner
            )
            > 0
        )
        pension_age_hb = pension_age_member_hb & ~reported(
            [
                "income_support_reported",
                "jsa_income_reported",
                "esa_income_reported",
            ]
        )
        # Art. 4(2) ends the saving once the couple is entitled to neither
        # benefit, which Universal Credit entitlement implies (TP Regs 2014
        # reg 5(1)(d)).
        receives_uc = reported(["universal_credit_reported"])
        # Art. 4(1) needs the couple to have been a mixed-age couple on
        # 14 May 2019, so its older member had reached the qualifying age by
        # then.
        older_member_qualified = benunit.any(
            claimant_or_partner
            & person("is_SP_age", period)
            & (person("birth_year", period) <= p.saving_latest_birth_year)
        )
        return (
            benunit("is_mixed_age_couple", period)
            & older_member_qualified
            & (reported(["pension_credit_reported"]) | pension_age_hb)
            & ~receives_uc
        )
