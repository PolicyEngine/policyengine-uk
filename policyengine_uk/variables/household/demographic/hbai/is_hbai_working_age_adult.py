from policyengine_uk.model_api import *


class is_hbai_working_age_adult(Variable):
    value_type = bool
    entity = Person
    label = "Working-age adult (HBAI definition)"
    documentation = (
        "Households Below Average Income defines working-age adults as all "
        "adults below State Pension age."
    )
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#working-age-adults"

    def formula(person, period, parameters):
        return person("is_hbai_adult", period) & ~person("is_SP_age", period)
