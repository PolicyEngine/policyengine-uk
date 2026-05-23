from policyengine_uk.model_api import *
import numpy as np


class cotswold_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Cotswold Council Tax Support tariff income from capital"
    definition_period = YEAR
    unit = GBP
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        tariff = parameters(
            period
        ).gov.local_authorities.cotswold.council_tax_reduction.means_test.tariff_income
        capital = benunit.household("savings", period)
        excess_capital = max_(0, capital - tariff.threshold)
        tariff_units = np.ceil(excess_capital / tariff.step)
        tariff_income = tariff_units * tariff.amount * WEEKS_IN_YEAR
        return where(has_uc_award, 0, tariff_income)
