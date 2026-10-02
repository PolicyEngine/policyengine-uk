from policyengine_uk.model_api import *


class ni_class_1_secondary_liable(Variable):
    label = "age-liable for secondary Class 1 NI"
    documentation = (
        "Whether this person's age allows secondary (employer) Class 1 "
        "contributions on their earnings. Secondary contributions are due on "
        "earners over 16 (SSCBA 1992 s.6(1)(b)). Unlike primary contributions, "
        "they continue after the earner reaches pensionable age (s.6(3))."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/6"

    def formula(person, period, parameters):
        return person("over_16", period)
