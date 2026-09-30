from policyengine_uk.model_api import *


class marriage_allowance_tax_reduction(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance tax reduction"
    documentation = (
        "The gaining party's tax reduction at Step 6 of the income tax "
        "calculation: the appropriate percentage of the transferable amount, "
        "capped at the tax left to reduce."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 55A(2)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55A",
        ),
        dict(
            title="Income Tax Act 2007 s. 55B(1) and (3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
        dict(
            title="Income Tax Act 2007 s. 29(2)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        reduction = person("marriage_allowance_appropriate_percentage", period) * (
            person("marriage_allowance", period)
        )
        return min_(reduction, person("marriage_allowance_tax_reduction_limit", period))
