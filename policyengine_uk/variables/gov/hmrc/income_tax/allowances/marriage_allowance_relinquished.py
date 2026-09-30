from policyengine_uk.model_api import *


class marriage_allowance_relinquished(Variable):
    value_type = float
    entity = Person
    label = "Personal allowance given up under a Marriage Allowance election"
    documentation = (
        "The transferable amount by which a Marriage Allowance election cuts "
        "the electing person's own personal allowance."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 55B(6)",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
    )
    unit = GBP

    def formula(person, period, parameters):
        return person("makes_marriage_allowance_election", period) * person(
            "marriage_allowance_transferable_amount", period
        )
