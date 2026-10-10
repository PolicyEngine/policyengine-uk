from policyengine_uk.model_api import *


class unused_pension_annual_allowance(Variable):
    label = "unused pension annual allowance brought forward"
    documentation = (
        "Unused annual allowance from the three previous tax years that is "
        "available for this tax year (FA 2004 s. 228A(5)): the amount by which "
        "each of those years' annual allowance exceeded the total pension "
        "input amount, for years in which the individual was a member of a "
        "registered pension scheme, less any part already used up in an "
        "intervening year (earliest year first). It increases this year's "
        "annual allowance (s. 228A(2)). Survey data does not record past "
        "pension input amounts, so this defaults to nil."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = dict(
        title="Finance Act 2004 s. 228A",
        href="https://www.legislation.gov.uk/ukpga/2004/12/section/228A",
    )
