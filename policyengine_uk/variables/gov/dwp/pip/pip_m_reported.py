from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class pip_m_reported(Variable):
    value_type = float
    entity = Person
    label = "PIP (mobility) (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"
