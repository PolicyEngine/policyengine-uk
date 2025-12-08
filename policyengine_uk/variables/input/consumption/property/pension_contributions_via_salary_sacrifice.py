from policyengine_uk.model_api import *


class pension_contributions_via_salary_sacrifice(Variable):
    label = "Pension contributions via salary sacrifice"
    documentation = (
        "Annual amount of pension contributions made through salary sacrifice "
        "arrangements, where the employee agrees to reduce their gross salary "
        "in exchange for employer pension contributions"
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://datacatalogue.ukdataservice.ac.uk/datasets/dataset/630d4a8d-ba6a-82b3-f33d-c713c66efcb3"
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"
