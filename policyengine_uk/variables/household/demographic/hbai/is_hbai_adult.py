from policyengine_uk.model_api import *


class is_hbai_adult(Variable):
    value_type = bool
    entity = Person
    label = "Adult (HBAI definition)"
    documentation = (
        "Households Below Average Income counts everyone who is not a "
        "dependent child as an adult."
    )
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#adult"

    def formula(person, period, parameters):
        return ~person("is_hbai_dependent_child", period)
