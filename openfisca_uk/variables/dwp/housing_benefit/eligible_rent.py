from openfisca_uk.model_api import *

class hb_eligible_rent(Variable):
    label = "Eligible rent"
    documentation = "Rent eligible for Housing Benefit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2006/213/part/3/made"

    formula = sum_of_variables(["benunit_rent"])
