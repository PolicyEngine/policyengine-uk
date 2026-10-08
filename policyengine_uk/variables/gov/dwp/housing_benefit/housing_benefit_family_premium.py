from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class housing_benefit_family_premium(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit family premium"
    documentation = "Separate from each child's personal allowance. Post-abolition entitlement requires the jurisdiction-specific pre-abolition award/family facts, continuing family condition and no new claim. The higher old lone-parent amount applies only to working-age claims with continuing 1998 protection."
    reference = (
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/3",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances.family_premium
        person = benunit.members
        has_child = benunit.any(
            person("is_child_or_young_person_for_legacy_benefits", period)
        )
        protected = (
            benunit("housing_benefit_family_premium_entitled_before_abolition", period)
            & benunit(
                "housing_benefit_family_premium_family_condition_continued", period
            )
            & ~benunit(
                "housing_benefit_family_premium_new_claim_since_abolition", period
            )
        )
        higher = (
            ~benunit("housing_benefit_pension_age_regulations_apply", period)
            & benunit("is_lone_parent", period)
            & benunit(
                "housing_benefit_lone_parent_family_premium_1998_protection", period
            )
        )
        amount = where(higher, p.protected_lone_parent, p.ordinary) * WEEKS_IN_YEAR
        country = benunit.household("country", period)
        ni = country == country.possible_values.NORTHERN_IRELAND
        total = 0
        for rules, share in fiscal_year_segments(
            parameters.gov.dwp.housing_benefit.allowances.family_premium.schedule,
            period.start.year,
        ):
            total += (
                has_child
                * (
                    where(ni, rules.ni_open_to_new_claims, rules.gb_open_to_new_claims)
                    | protected
                )
                * amount
                * share
            )
        return total
