from policyengine_uk.model_api import *


class bath_and_north_east_somerset_council_tax_reduction_excess_income_reduction(
    Variable
):
    value_type = float
    entity = BenUnit
    label = "Bath and North East Somerset Council Tax Reduction excess-income reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bathnes.gov.uk/sites/default/files/2026-01/Council_Tax_reduction_scheme_April_1_2026_to_March_31_2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.bath_and_north_east_somerset.council_tax_reduction
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        applicable_income = benunit(
            "council_tax_reduction_applicable_income", period
        ) + benunit(
            "bath_and_north_east_somerset_council_tax_reduction_tariff_income", period
        )
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        excess_income = max_(0, applicable_income - applicable_amount)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        return where(has_uc_award, 0, excess_income * ctr.means_test.withdrawal_rate)
