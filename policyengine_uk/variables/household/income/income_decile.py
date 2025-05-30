from policyengine_uk.model_api import *
import datetime
import numpy as np


class income_decile(Variable):
    label = "income decile"
    documentation = "Decile of household net income. Households are sorted by disposable income, and then divided into 10 equally-populated groups."
    entity = Person
    definition_period = YEAR
    value_type = int

    def formula(person, period, parameters):
        return person.household("household_income_decile", period)
