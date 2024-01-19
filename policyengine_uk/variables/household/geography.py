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
        if (
            hasattr(household.simulation, "dataset")
            and household.simulation.dataset.name == "enhanced_frs"
        ):
            from policyengine_uk.data.gov import enhanced_frs_brmas

            return np.array(
                [getattr(BRMAName, x) for x in enhanced_frs_brmas.brma.values]
            )
        else:
            return np.array([BRMAName.MAIDSTONE] * household.count)


class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.LONDON
    entity = Household
    label = "region"
    documentation = "Area of the UK"
    definition_period = YEAR
