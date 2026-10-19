from policyengine_uk.model_api import *


class war_widows_pension(Variable):
    value_type = float
    entity = Person
    label = "War Widow's or Widower's Pension"
    definition_period = YEAR
    unit = GBP

    adds = ["war_widows_pension_reported"]
