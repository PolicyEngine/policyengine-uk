from policyengine_uk.model_api import *


class bsp_calculated(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = FLOW
    unit = GBP
    label = "BSP calculated"
    documentation = "Additional calculated cash; opt-in/defined_for bsp_add_calculated_award; sums initial and monthly components. No additional independent budget/head/HBAI term."
    reference = (
        "https://www.gov.uk/bereavement-support-payment/what-youll-get",
        "https://www.nidirect.gov.uk/articles/bereavement-support-payment",
        "https://www.legislation.gov.uk/uksi/2017/410/regulation/3",
    )

    defined_for = "bsp_add_calculated_award"
    adds = ["bsp_calculated_initial_payment", "bsp_calculated_monthly_payments"]
