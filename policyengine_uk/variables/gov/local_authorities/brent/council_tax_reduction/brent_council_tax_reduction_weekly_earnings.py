from policyengine_uk.model_api import *


class brent_council_tax_reduction_weekly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Brent Council Tax Support weekly claimant and partner earnings"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        gross_earnings = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + person("self_employment_income", period)
            )
        )
        has_uc = benunit("universal_credit", period) > 0
        uc_earnings = benunit("uc_earned_income", period)
        annual_earnings = where(has_uc, uc_earnings, gross_earnings)
        return annual_earnings / WEEKS_IN_YEAR
