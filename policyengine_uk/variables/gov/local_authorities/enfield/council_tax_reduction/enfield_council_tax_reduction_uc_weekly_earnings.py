from policyengine_uk.model_api import *


class enfield_council_tax_reduction_uc_weekly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Enfield CTR Universal Credit weekly net earnings"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        gross_earnings = benunit.sum(
            claimant_or_partner * person("uc_mif_capped_earned_income", period)
        )
        deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period)
            )
        )
        return max_(0, gross_earnings - deductions) / WEEKS_IN_YEAR
