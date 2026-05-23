from policyengine_uk.model_api import *


class babergh_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Babergh Council Tax Reduction tariff income"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.babergh.gov.uk/documents/d/babergh/bdc-ctr-scheme-2026_27-v4-pdf"
    )

    def formula(benunit, period, parameters):
        tariff = parameters(
            period
        ).gov.local_authorities.babergh.council_tax_reduction.means_test.tariff_income
        capital = benunit.household("savings", period)
        tariff_units = np.ceil(max_(0, capital - tariff.threshold) / tariff.step)
        tariff_income = tariff_units * tariff.amount * WEEKS_IN_YEAR
        has_uc_award = benunit("universal_credit", period) > 0
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(has_uc_award | relevant_income_based_benefit, 0, tariff_income)
