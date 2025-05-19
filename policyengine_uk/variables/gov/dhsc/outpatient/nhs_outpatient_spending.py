from policyengine_uk.model_api import *


class nhs_outpatient_spending(Variable):
    label = "NHS spending on outpatient visits"
    documentation = (
        "Total spending by the NHS on outpatient visits for this person."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
