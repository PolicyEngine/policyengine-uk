from policyengine_uk.model_api import *
import numpy as np


class squared_poverty_gap_bhc(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = "/1"
    label = "Normalized squared poverty gap, before housing costs"
    documentation = (
        "Dimensionless household FGT2 component: the square of the existing "
        "before housing costs poverty gap divided by its matching poverty line. "
        "Uses the existing HBAI income basis; a nonpositive line is undefined "
        "and returns NaN."
    )
    reference = "https://worldbank.github.io/PIP-Methodology-2022-05/surveyestimates.html#monetarypoverty"

    def formula(household, period, parameters):
        gap = household("poverty_gap_bhc", period)
        line = household("poverty_line_bhc", period)
        normalized_gap = np.divide(
            gap,
            line,
            out=np.full_like(gap, np.nan, dtype=float),
            where=line > 0,
        )
        return np.square(normalized_gap)
