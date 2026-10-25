from policyengine_uk.model_api import *


class poverty_threshold_fye2011_bhc(Variable):
    label = "Poverty threshold on the FYE 2011 reference line (BHC)"
    documentation = (
        "The absolute poverty line before housing costs for a couple with no "
        "children, per year, on the FYE 2011 reference: 60% of the FYE 2011 "
        "median held constant in real terms, in every year. HBAI used this "
        "line until March 2026, and most earlier published absolute poverty "
        "estimates use it. poverty_threshold_bhc is HBAI's current line, "
        "on the FYE 2025 reference from FYE 2022."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return (
            parameters(period).household.poverty.absolute_poverty_threshold_fye2011_bhc
            * WEEKS_IN_YEAR
        )
