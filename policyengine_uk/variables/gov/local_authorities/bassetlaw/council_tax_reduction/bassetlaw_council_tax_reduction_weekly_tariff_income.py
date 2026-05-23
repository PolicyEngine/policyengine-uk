from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_weekly_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Bassetlaw Council Tax Reduction weekly tariff income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.bassetlaw.council_tax_reduction
        capital = benunit.household("savings", period)
        return np.ceil(
            max_(0, capital - ctr.means_test.tariff_income_threshold)
            / ctr.means_test.tariff_income_increment
        )
