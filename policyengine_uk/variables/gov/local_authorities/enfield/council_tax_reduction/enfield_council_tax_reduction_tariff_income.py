from policyengine_uk.model_api import *
import numpy as np


class enfield_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Enfield CTR tariff income from capital"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        tariff = parameters(
            period
        ).gov.local_authorities.enfield.council_tax_reduction.means_test.tariff_income
        capital = benunit.household("savings", period)
        excess_capital = max_(0, capital - tariff.threshold)
        tariff_units = np.ceil(excess_capital / tariff.step)
        return tariff_units * tariff.amount * WEEKS_IN_YEAR
