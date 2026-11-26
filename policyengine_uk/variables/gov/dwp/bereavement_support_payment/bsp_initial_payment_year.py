from policyengine_uk.model_api import *


class bsp_initial_payment_year(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = STOCK
    label = "BSP initial payment year"
    documentation = "Fixed actual fiscal/model receipt year of the independently qualified initial payment;0unknown/not paid. Never substitute current year or assume claim/death year. These fixed actual receipt facts require genuine supplied provenance; current-year defaults, calculated caches and imputed dates are not evidence."
    reference = (
        "https://www.gov.uk/bereavement-support-payment/what-youll-get",
        "https://www.nidirect.gov.uk/articles/bereavement-support-payment",
        "https://www.legislation.gov.uk/uksi/2017/410/regulation/3",
    )
