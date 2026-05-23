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

        personal_pension_band_extension = min_(
            person("personal_pension_contributions", period),
            person("pension_contributions_relief", period),
        )
        basic_rate_band_extension = (
            person("gift_aid_grossed_up", period) + personal_pension_band_extension
        )
        allowances_for_cgt_income = max_(
            0,
            person("allowances", period)
            - person("gift_aid", period)
            - personal_pension_band_extension,
        )
        taxable_income = max_(
            0,
            person("adjusted_net_income", period) - allowances_for_cgt_income,
        )
        gains = max_(0, person("capital_gains", period))
        aea = cgt.annual_exempt_amount
        gains_less_aea = max_(0, gains - aea)
        basic_rate_limit = it.rates.uk.thresholds[1] + basic_rate_band_extension
        remaining_basic_rate_band = max_(basic_rate_limit - taxable_income, 0)

        basic_rate_applicable_cg = min_(gains_less_aea, remaining_basic_rate_band)
        higher_and_add_rate_applicable_cg = max_(
            gains_less_aea - remaining_basic_rate_band, 0
        )
        higher_rate_limit = it.rates.uk.thresholds[2] + basic_rate_band_extension
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
