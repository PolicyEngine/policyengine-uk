from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "South Derbyshire Council Tax Reduction tariff income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.south_derbyshire.council_tax_reduction
        capital = benunit(
            "south_derbyshire_council_tax_reduction_assessable_capital", period
        )
        weekly_tariff_income = np.ceil(
            max_(0, capital - ctr.means_test.tariff_income_threshold)
            / ctr.means_test.tariff_income_increment
        )
        return weekly_tariff_income * WEEKS_IN_YEAR
