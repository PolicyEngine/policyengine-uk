from policyengine_uk.model_api import *


class statutory_sick_pay(Variable):
    value_type = float
    entity = Person
    label = "Statutory Sick Pay"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Social Security Contributions and Benefits Act 1992, Part XI",
        href="http://www.legislation.gov.uk/ukpga/1992/4/part/XI",
    )
