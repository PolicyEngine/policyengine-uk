from policyengine_uk.model_api import *


class is_hbai_pensioner(Variable):
    value_type = bool
    entity = Person
    label = "Pensioner (HBAI definition)"
    documentation = (
        "Households Below Average Income defines pensioners as all adults at "
        "or above State Pension age, classified individually."
    )
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#pensioner"

    def formula(person, period, parameters):
        return person("is_hbai_adult", period) & person("is_SP_age", period)
