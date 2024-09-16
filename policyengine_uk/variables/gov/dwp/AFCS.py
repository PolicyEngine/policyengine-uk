from policyengine_uk.model_api import *


class afcs(Variable):
    value_type = float
    entity = Person
    label = "Armed Forces Compensation Scheme"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.benefit_uprating_cpi"

    adds = ["afcs_reported"]


class afcs_reported(Variable):
    value_type = float
    entity = Person
    label = "Armed Forces Compensation Scheme (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.benefit_uprating_cpi"
