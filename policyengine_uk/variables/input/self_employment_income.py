from policyengine_uk.model_api import *


class self_employment_income(Variable):
    value_type = float
    entity = Person
    label = "self-employment income"
    documentation = "Income from self-employment profits. This should be net of self-employment expenses."
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.per_capita.mixed_income"
