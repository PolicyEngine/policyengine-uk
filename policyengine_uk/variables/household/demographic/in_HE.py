from policyengine_uk.model_api import *
import pandas as pd


class in_HE(Variable):
    value_type = bool
    entity = Person
    label = "In higher education"
    definition_period = YEAR
    reference = "Whether this person is in Higher Education"
    set_input = set_input_dispatch_by_period
