from policyengine_uk.model_api import *


class poverty_threshold_ahc(Variable):
    label = "Poverty threshold on HBAI's current reference line (AHC)"
    documentation = (
        "The absolute poverty line after housing costs for a couple with no "
        "children, per year: 60% of the FYE 2025 median (FYE 2011 before "
        "FYE 2022), held constant in real terms. "
        "Compare against equivalised income; poverty_line_ahc is the same "
        "line scaled to the household's equivalisation factor."
        " The FYE 2011 reference line in every year is poverty_threshold_fye2011_ahc."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return (
            parameters(period).household.poverty.absolute_poverty_threshold_ahc
            * WEEKS_IN_YEAR
        )
