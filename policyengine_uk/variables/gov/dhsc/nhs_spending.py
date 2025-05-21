from policyengine_uk.model_api import *


class nhs_spending(Variable):
    label = "NHS spending"
    documentation = "Total NHS spending for this person."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "nhs_outpatient_spending",
        "nhs_a_and_e_spending",
        "nhs_admitted_patient_spending",
    ]
