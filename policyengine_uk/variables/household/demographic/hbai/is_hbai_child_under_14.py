from policyengine_uk.model_api import *


class is_hbai_child_under_14(Variable):
    value_type = bool
    entity = Person
    label = "Dependent child under 14 (HBAI equivalence scale)"
    documentation = (
        "A dependent child below the older-child age of the HBAI modified "
        "OECD equivalence scale."
    )
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#equivalisation-1"

    def formula(person, period, parameters):
        threshold = parameters(period).household.demographic.equiv.child_age_threshold
        return person("is_hbai_dependent_child", period) & (
            person("age", period) < threshold
        )
