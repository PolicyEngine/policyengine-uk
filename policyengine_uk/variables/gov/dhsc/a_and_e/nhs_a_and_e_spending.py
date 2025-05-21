from policyengine_uk.model_api import *


class nhs_a_and_e_spending(Variable):
    label = "NHS spending on A&E visits"
    documentation = "Total spending by the NHS on A&E visits for this person."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
