from policyengine_uk.model_api import *
import pandas as pd


class person_id(Variable):
    value_type = int
    entity = Person
    label = "ID for the person"
    definition_period = YEAR
