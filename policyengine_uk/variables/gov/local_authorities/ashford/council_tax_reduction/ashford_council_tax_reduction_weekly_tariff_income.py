from policyengine_uk.model_api import *


class ashford_council_tax_reduction_weekly_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction weekly tariff income"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.ashford.council_tax_reduction
        capital = benunit.household("savings", period)
        return np.ceil(
            max_(0, capital - ctr.means_test.tariff_income_threshold)
            / ctr.means_test.tariff_income_increment
        )
