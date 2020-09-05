from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

class age_band(Variable):
    value_type = int
    entity = Person
    label = u'FRS-encoded age band'
    definition_period = ETERNITY

class age(Variable):
    value_type = int
    entity = Person
    label = u'Likely age from FRS codes'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        band = person('age_band', period)
        return (band == 4) * 18 + (band == 5) * 23 + (band == 6) * 27 + (band == 7) * 33 + (band == 8) * 37 + (band == 9) * 43 + (band == 10) * 47 + (band == 11) * 53 + (band == 12) * 57 + (band == 13) * 63 + (band == 14) * 67 + (band == 15) * 73 + (band == 16) * 80