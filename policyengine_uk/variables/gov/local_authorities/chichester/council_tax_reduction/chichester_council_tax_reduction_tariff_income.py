from policyengine_uk.model_api import *
import numpy as np


class chichester_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Chichester Council Tax Reduction tariff income"
    definition_period = YEAR
    unit = GBP
    reference = "https://chichester.moderngov.co.uk/documents/s30863/09.1%20Appendix%201%20Local%20Council%20Tax%20Reduction%20Scheme%20Rules%202026%20-%202027.pdf"

    def formula(benunit, period, parameters):
        tariff = parameters(
            period
        ).gov.local_authorities.chichester.council_tax_reduction.means_test.tariff_income
        capital = benunit.household("savings", period)
        tariff_units = np.ceil(max_(0, capital - tariff.threshold) / tariff.step)
        tariff_income = tariff_units * tariff.amount * WEEKS_IN_YEAR
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(has_uc_award | relevant_income_based_benefit, 0, tariff_income)
