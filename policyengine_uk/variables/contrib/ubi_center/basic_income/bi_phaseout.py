from policyengine_uk.model_api import *


class bi_phaseout(Variable):
    label = "Basic income phase-out"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["bi_individual_phaseout", "bi_household_phaseout"]
