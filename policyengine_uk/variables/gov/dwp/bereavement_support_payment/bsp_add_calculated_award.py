from policyengine_uk.model_api import *


class bsp_add_calculated_award(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "BSP add calculated award"
    documentation = "Operational opt-in: this calculated award is verified additional to and disjoint from bsp_reported and separately reported WPA/war-pension/residual cash. Never replace or guess a mixed reported cell."
    reference = (
        "https://www.gov.uk/bereavement-support-payment/what-youll-get",
        "https://www.nidirect.gov.uk/articles/bereavement-support-payment",
        "https://www.legislation.gov.uk/uksi/2017/410/regulation/3",
    )
