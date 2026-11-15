from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.housing_benefit_family_premium_category import (
    HousingBenefitFamilyPremiumCategory,
)


class housing_benefit_family_premium(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit protected family premium"
    documentation = (
        "Ordinary family premium before the new-claim closure year; from "
        "that year it requires the pre-assessed protection category. At least "
        "one legally included child or young person is required. The higher "
        "historical lone-parent rate is restricted to the working-age "
        "schedule and current lone parents. Claim continuity and within-year "
        "claim dates are not inferred from current household composition."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/part/2/2015-04-06",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/part/2/2015-04-06",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/part/II/2015-04-06",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4/part/II/2015-04-06",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.premiums.family
        category = benunit("housing_benefit_family_premium_category", period)
        categories = HousingBenefitFamilyPremiumCategory
        child = benunit.members("is_child_or_young_person_for_legacy_benefits", period)
        country = benunit.household("country", period)
        # The closure year contains both pre- and post-closure claims. From
        # that year, the category must establish legal protection rather
        # than treating all claims as having begun before the cutoff.
        before_closure_year = where(
            country == country.possible_values.NORTHERN_IRELAND,
            period.start.year < p.new_claim_end.northern_ireland // 10000,
            period.start.year < p.new_claim_end.great_britain // 10000,
        )
        eligible = benunit.any(child) & (
            before_closure_year | (category != categories.NONE)
        )
        historical_lone_parent = (
            (category == categories.HISTORICAL_LONE_PARENT_PROTECTED)
            & benunit("is_lone_parent", period)
            & ~benunit("housing_benefit_pension_age_regulations_apply", period)
        )
        weekly = where(historical_lone_parent, p.lone_parent_protected_amount, p.amount)
        return where(eligible, weekly * WEEKS_IN_YEAR, 0)
