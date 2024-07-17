from policyengine_uk.model_api import *


class pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Amount contributed to registered pension schemes paid by the individual (not the employer)"
    definition_period = YEAR
    unit = GBP

    adds = "gov.hmrc.pensions.pensions_programs"
