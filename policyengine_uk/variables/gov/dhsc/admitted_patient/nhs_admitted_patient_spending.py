from policyengine_uk.model_api import *


class nhs_admitted_patient_spending(Variable):
    label = "NHS spending on admitted patient visits"
    documentation = (
        "Total spending by the NHS on admitted patient visits for this person."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
