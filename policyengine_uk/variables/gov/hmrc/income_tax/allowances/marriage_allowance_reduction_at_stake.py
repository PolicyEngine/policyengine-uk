from policyengine_uk.model_api import *


class marriage_allowance_reduction_at_stake(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance tax reduction at stake in the share of deductions"
    documentation = (
        "The Marriage Allowance tax reduction this person receives only if "
        "the share of reliefs and allowances meets the income conditions "
        "(ITA 2007 s. 55B(2)(b) and (ba)): the appropriate percentage of the "
        "allowance they would then receive (s. 55B(1) and (3)), before the "
        "limit of the Step 5 tax left. The search for that share (s. 25(2)) "
        "weighs it, and a reform that gives the allowance at any share sets "
        "it to nil."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 55B",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
        dict(
            title="Income Tax Act 2007 s. 25(2)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        return person("marriage_allowance_appropriate_percentage", period) * person(
            "marriage_allowance_if_income_conditions_met", period
        )
