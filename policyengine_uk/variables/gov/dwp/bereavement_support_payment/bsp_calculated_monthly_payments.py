from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.bereavement_support_payment.bsp_calculated_initial_payment import (
    bsp_input_periods,
)


class bsp_calculated_monthly_payments(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = FLOW
    unit = GBP
    label = "BSP calculated monthly payments"
    documentation = "Separate qualified standard/higher counts times source amounts. Both counts nonnegative, history known0..18 and combined counts<=18-history. Reject inconsistent allocation to zero monthly cash instead of inventing order/rate trimming. No12cash-year cap."
    reference = (
        "https://www.gov.uk/bereavement-support-payment/what-youll-get",
        "https://www.nidirect.gov.uk/articles/bereavement-support-payment",
        "https://www.legislation.gov.uk/uksi/2017/410/regulation/3",
    )

    def formula_2017_01_01(person, period, parameters):
        names = (
            "bsp_standard_instalments",
            "bsp_higher_instalments",
            "bsp_instalments_received_before_year",
        )
        if not all(period in bsp_input_periods(person, name) for name in names):
            return person.empty_array()
        p = parameters(period).gov.dwp.bsp
        standard = person("bsp_standard_instalments", period)
        higher = person("bsp_higher_instalments", period)
        previous = person("bsp_instalments_received_before_year", period)
        valid = (
            (standard >= 0)
            & (higher >= 0)
            & (previous >= 0)
            & (previous <= p.maximum_instalments)
            & (standard + higher <= p.maximum_instalments - previous)
        )
        amount = (
            standard * p.standard_monthly_payment + higher * p.higher_monthly_payment
        )
        # Inconsistent history does not establish which rate was received first.
        return where(valid, amount, 0)
