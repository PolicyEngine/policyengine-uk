from policyengine_uk.model_api import *
import pandas as pd


class in_social_housing(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person lives in social housing"
    definition_period = YEAR

    def formula(person, period, parameters):
        tenure = person.household("tenure_type", period.this_year)
        tenures = tenure.possible_values
        return is_in(tenure, tenures.RENT_FROM_COUNCIL, tenures.RENT_FROM_HA)
