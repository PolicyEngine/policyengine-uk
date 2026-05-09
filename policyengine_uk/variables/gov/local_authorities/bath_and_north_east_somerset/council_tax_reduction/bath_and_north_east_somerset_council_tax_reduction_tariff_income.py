from policyengine_uk.model_api import *
import numpy as np


class bath_and_north_east_somerset_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Bath and North East Somerset Council Tax Reduction tariff income from capital"
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bathnes.gov.uk/sites/default/files/2026-01/Council_Tax_reduction_scheme_April_1_2026_to_March_31_2027.pdf"

    def formula(benunit, period, parameters):
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        tariff = parameters(
            period
        ).gov.local_authorities.bath_and_north_east_somerset.council_tax_reduction.means_test.tariff_income
        capital = benunit.household("savings", period)
        excess_capital = max_(0, capital - tariff.threshold)
        tariff_units = np.floor(excess_capital / tariff.step)
        tariff_income = tariff_units * tariff.amount * WEEKS_IN_YEAR
        return where(has_uc_award | relevant_income_based_benefit, 0, tariff_income)
