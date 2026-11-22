from policyengine_uk.model_api import *


class firm_paybill_after_minimum_wage(Variable):
    value_type = float
    entity = Firm
    label = "Firm paybill after the minimum wage"
    documentation = (
        "firm_paybill plus firm_minimum_wage_cost: the paybill once the "
        "low-paid workers are paid at least the adult minimum wage. The "
        "apprenticeship levy and the default employer National Insurance "
        "and auto-enrolment approximations read it. Where the pay data "
        "already comply, it equals firm_paybill."
    )
    definition_period = YEAR
    unit = GBP
    adds = ["firm_paybill", "firm_minimum_wage_cost"]
