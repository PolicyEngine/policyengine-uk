from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.locations import BRMAName
from policyengine_uk.variables.household.demographic.geography import Region
from policyengine_uk.utils.geography import resolved_region
import pandas as pd
import numpy as np


class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.LONDON
    entity = Household
    label = "region"
    documentation = (
        "Area of the UK. The later genuine region or council source wins "
        "by source start and stop; equal periods prefer region, including "
        "UNKNOWN. A country supplied for the requested year is a fallback "
        "when neither applies. With none supplied, the default is London."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        return resolved_region(household, period)
