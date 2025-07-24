from policyengine_uk.model_api import *


class employer_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Employer pension contributions"
    documentation = "Total amount spent on employer pension contributions"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"
