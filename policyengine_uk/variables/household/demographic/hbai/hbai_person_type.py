from policyengine_uk.model_api import *


class HBAIPersonType(Enum):
    CHILD = "Dependent child"
    WORKING_AGE_ADULT = "Working-age adult"
    PENSIONER = "Pensioner"


class hbai_person_type(Variable):
    value_type = Enum
    possible_values = HBAIPersonType
    default_value = HBAIPersonType.WORKING_AGE_ADULT
    entity = Person
    label = "Population group (HBAI definition)"
    documentation = (
        "The Households Below Average Income population groups: dependent "
        "children, working-age adults (below State Pension age) and "
        "pensioners (at or above State Pension age). Every person is in "
        "exactly one group."
    )
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#child"

    def formula(person, period, parameters):
        return select(
            [
                person("is_hbai_dependent_child", period),
                person("is_hbai_working_age_adult", period),
            ],
            [HBAIPersonType.CHILD, HBAIPersonType.WORKING_AGE_ADULT],
            default=HBAIPersonType.PENSIONER,
        )
