from policyengine_uk.model_api import *
import datetime
import numpy as np


class is_apprentice(Variable):
    value_type = bool
    entity = Person
    label = "In an apprenticeship programme"
    definition_period = YEAR
    default_value = False
