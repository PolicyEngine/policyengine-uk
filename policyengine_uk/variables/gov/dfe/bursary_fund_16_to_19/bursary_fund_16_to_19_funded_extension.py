from policyengine_uk.model_api import *


class bursary_fund_16_to_19_funded_extension(Variable):
    value_type = bool
    entity = Person
    label = "Uses the 19 to 24 funded extension for 16 to 19 Bursary Fund"
    documentation = (
        "Whether the student is aged 19 to 24 and funded from the 16 to 19 budget, "
        "for example due to an EHC plan or eligible continuing study."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period
