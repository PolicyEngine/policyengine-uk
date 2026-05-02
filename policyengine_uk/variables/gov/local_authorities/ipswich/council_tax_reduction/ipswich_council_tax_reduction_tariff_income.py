from policyengine_uk.model_api import *


class ipswich_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Ipswich Council Tax Reduction tariff income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.ipswich.gov.uk/sites/ipswich/files/2026-03/Council%20Tax%20Reduction%20scheme%202026_0.pdf"

    def formula(benunit, period, parameters):
        tariff = parameters(
            period
        ).gov.local_authorities.ipswich.council_tax_reduction.means_test.tariff_income
        capital = benunit.household("savings", period)
        tariff_units = np.ceil(max_(0, capital - tariff.threshold) / tariff.step)
        tariff_income = tariff_units * tariff.amount * WEEKS_IN_YEAR
        has_uc_award = benunit("universal_credit", period) > 0
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(has_uc_award | relevant_income_based_benefit, 0, tariff_income)
