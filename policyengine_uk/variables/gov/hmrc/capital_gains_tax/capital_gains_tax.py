from policyengine_uk.model_api import *
from policyengine_core.holders import Holder


class capital_gains_tax(Variable):
    label = "capital gains tax"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        hmrc = parameters(period).gov.hmrc
        cgt = hmrc.cgt
        it = hmrc.income_tax

        ani = person("adjusted_net_income", period)
        gains = max_(0, person("capital_gains", period))
        aea = cgt.annual_exempt_amount
        gains_less_aea = max_(0, gains - aea)
        basic_rate_limit = it.rates.uk.thresholds[1]
        remaining_basic_rate_band = max_(basic_rate_limit - ani, 0)

        basic_rate_applicable_cg = min_(
            gains_less_aea, remaining_basic_rate_band
        )
        higher_and_add_rate_applicable_cg = max_(
            gains_less_aea - remaining_basic_rate_band, 0
        )
        higher_rate_limit = it.rates.uk.thresholds[2]
        higher_rate_applicable_cg = min_(
            higher_and_add_rate_applicable_cg,
            higher_rate_limit - basic_rate_limit,
        )
        add_rate_applicable_cg = max_(
            higher_and_add_rate_applicable_cg - higher_rate_applicable_cg, 0
        )

        basic_rate_tax = basic_rate_applicable_cg * cgt.basic_rate
        higher_rate_tax = higher_rate_applicable_cg * cgt.higher_rate
        add_rate_tax = add_rate_applicable_cg * cgt.additional_rate

        return basic_rate_tax + higher_rate_tax + add_rate_tax
