from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class beer_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Alcohol duty on beer"
    reference = "https://www.legislation.gov.uk/ukpga/2023/30/schedule/7"

    def formula_2024(household, period, parameters):
        p = parameters(period).gov.hmrc.alcohol_duty
        litres = max_(household("beer_litres", period), 0)
        abv = clip(household("beer_abv", period), 0, 1)
        draught = clip(household("beer_draught_share", period), 0, 1)
        total = 0
        for rates, share in fiscal_year_segments(
            parameters.gov.hmrc.alcohol_duty.rates, period.start.year
        ):
            standard = rates.beer
            draught_rate = rates.draught_other
            rate = select(
                [
                    abv <= p.taxable_abv,
                    abv < p.standard_abv,
                    abv < p.high_abv,
                    abv <= p.spirits_abv,
                ],
                [
                    0,
                    rates.low * (1 - draught) + rates.draught_low * draught,
                    standard * (1 - draught) + draught_rate * draught,
                    rates.high,
                ],
                default=rates.spirits,
            )
            strength = abv
            total += litres * strength * rate * share
        return total
