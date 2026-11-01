from policyengine_uk.model_api import *


class is_full_year_category_a_director(Variable):
    label = "Full-year category A director, one employment (employee NI, 2022–23 only)"
    documentation = (
        "For employee NI only, explicitly declares directorship throughout the tax year, one employment "
        "and category A throughout. Only model year 2022 uses this fact. It does "
        "not describe appointment years, other categories or payroll timing."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    default_value = False
    reference = [
        "https://www.gov.uk/employee-directors",
        "https://www.gov.uk/guidance/rates-and-thresholds-for-employers-2022-to-2023",
    ]
