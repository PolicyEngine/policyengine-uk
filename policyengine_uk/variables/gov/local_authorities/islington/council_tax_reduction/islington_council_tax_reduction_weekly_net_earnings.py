from policyengine_uk.model_api import *


class islington_council_tax_reduction_weekly_net_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Islington CTR weekly net earnings"
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
        earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period)
            )
        )
        standard_net_earnings = max_(0, gross_earnings - earnings_deductions)
        has_uc = benunit("universal_credit", period) > 0
        uc_net_earnings = max_(
            0,
            add(benunit, period, ["uc_mif_capped_earned_income"]) - earnings_deductions,
        )
        return where(has_uc, uc_net_earnings, standard_net_earnings) / WEEKS_IN_YEAR
