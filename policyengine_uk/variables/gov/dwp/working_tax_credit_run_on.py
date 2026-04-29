from policyengine_uk.model_api import *


class working_tax_credit_run_on(Variable):
    value_type = bool
    entity = BenUnit
    label = "Working Tax Credit run-on"
    documentation = "Whether this benefit unit receives Working Tax Credit run-on."
    definition_period = YEAR
    reference = (
        "The Local Authority (Duty to Secure Early Years Provision Free of Charge) "
        "(Amendment) Regulations 2018, regulation 2(a)(i)"
    )
