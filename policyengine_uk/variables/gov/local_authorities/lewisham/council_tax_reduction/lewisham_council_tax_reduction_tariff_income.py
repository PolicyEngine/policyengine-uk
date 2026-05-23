from policyengine_uk.model_api import *
import numpy as np


class lewisham_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Lewisham Council Tax Reduction tariff income from capital"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        has_uc_case = benunit("universal_credit", period) > 0
        tariff = parameters(
            period
        ).gov.local_authorities.lewisham.council_tax_reduction.means_test.tariff_income
        capital = benunit.household("savings", period)
        excess_capital = max_(0, capital - tariff.threshold)
        tariff_units = np.ceil(excess_capital / tariff.step)
        tariff_income = tariff_units * tariff.amount * WEEKS_IN_YEAR
        return where(has_uc_case, 0, tariff_income)
