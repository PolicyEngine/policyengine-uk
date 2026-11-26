from policyengine_uk.model_api import *


def bsp_input_periods(person, name):
    """Return genuinely supplied periods, excluding calculated holder caches."""
    return person.get_holder(name).get_input_periods(person.simulation.branch_name)


class bsp_calculated_initial_payment(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = FLOW
    unit = GBP
    label = "BSP calculated initial payment"
    documentation = "Source-parametrised initial award only at its fixed actual receipt year and known category; no recurring initial payment."
    reference = (
        "https://www.gov.uk/bereavement-support-payment/what-youll-get",
        "https://www.nidirect.gov.uk/articles/bereavement-support-payment",
        "https://www.legislation.gov.uk/uksi/2017/410/regulation/3",
    )

    def formula_2017_01_01(person, period, parameters):
        if not bsp_input_periods(
            person, "bsp_initial_payment_year"
        ) or not bsp_input_periods(person, "bsp_initial_payment_rate"):
            return person.empty_array()
        p = parameters(period).gov.dwp.bsp
        paid_year = person("bsp_initial_payment_year", period)
        rate = person("bsp_initial_payment_rate", period)
        categories = rate.possible_values
        amount = select(
            [rate == categories.STANDARD, rate == categories.HIGHER],
            [p.standard_initial_payment, p.higher_initial_payment],
            default=0,
        )
        return (paid_year == period.start.year) * amount
