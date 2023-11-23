from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.locations import BRMAName
from policyengine_uk.variables.household.demographic.geography import Region
import pandas as pd
import numpy as np

label = "Geography"
index = -1


class BRMA(Variable):
    value_type = Enum
    possible_values = BRMAName
    default_value = BRMAName.MAIDSTONE
    entity = Household
    label = "Broad Rental Market Area"
    definition_period = YEAR

    def formula(household, period, parameters):
        from policyengine_uk.data.gov import lha_list_of_rents
        country = household("country", period)
        # Sample from a random BRMA, weighted by the number of observations in each BRMA

        brma = lha_list_of_rents.brma.sample(n=len(country))

        encoded_brma = [getattr(BRMAName, x) for x in brma]
        # Also todo: within region and lha category.
        return np.array(encoded_brma)



class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.LONDON
    entity = Household
    label = "region"
    documentation = "Area of the UK"
    definition_period = YEAR
