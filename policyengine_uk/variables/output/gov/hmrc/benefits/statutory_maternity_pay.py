from policyengine_uk.model_api import *


class statutory_maternity_pay(Variable):
    value_type = float
    entity = Person
    label = "Statutory Maternity Pay"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Social Security Contributions and Benefits Act 1992, Part XII",
        href="http://www.legislation.gov.uk/ukpga/1992/4/part/XII",
    )
