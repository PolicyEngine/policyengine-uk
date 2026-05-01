from policyengine_uk.model_api import *


class kingston_upon_hull_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Kingston upon Hull Council Tax Reduction Universal Credit applicable income"
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.hull.gov.uk/downloads/file/239/council-tax-reduction-scheme-2025-to-2026"

    def formula(benunit, period, parameters):
        has_uc_award = benunit("universal_credit", period) > 0
        uc_income = benunit("uc_earned_income", period) + benunit(
            "uc_unearned_income", period
        )
        uc_award = benunit("universal_credit", period)
        return has_uc_award * (uc_income + uc_award)
