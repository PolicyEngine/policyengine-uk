from policyengine_uk.model_api import *
import pandas as pd


class in_FE(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is in Further Education"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period
