from policyengine_uk.model_api import *


class ni_liable(Variable):
    label = "age-liable for primary Class 1 and Class 2 NI"
    documentation = (
        "Whether this person's age allows primary (employee) Class 1 and "
        "Class 2 contributions: 16 or over and under state pension age. "
        "Primary Class 1 ends at pensionable age (SSCBA 1992 s.6(3)) and Class "
        "2 after the week the earner reaches it (s.11(7)(b)). The model "
        "applies both with the annual is_SP_age flag. Class 4 ends for anyone "
        "over pensionable age at the start of the tax year (SI 2001/1004 reg "
        "91(a)); see ni_class_4_liable. Secondary (employer) Class 1 has no "
        "upper age limit; see ni_class_1_secondary_liable."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = [
        "https://www.legislation.gov.uk/ukpga/1992/4/section/6",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/11",
    ]

    def formula(person, period, parameters):
        return person("over_16", period) & ~person("is_SP_age", period)
