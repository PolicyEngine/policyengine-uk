from policyengine_uk.model_api import *


class marriage_allowance_tax_reduction_limit(Variable):
    value_type = float
    entity = Person
    label = "Tax available for the Marriage Allowance reduction"
    documentation = (
        "Tax at Step 5 of the income tax calculation left after the person's "
        "other tax reductions. The Marriage Allowance tax reduction cannot "
        "exceed it. Deducting the other reductions first gives the same total "
        "as the order that most reduces the person's liability."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 29(2) and (3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
        dict(
            title="Income Tax Act 2007 s. 27(2)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/27",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        step_5_tax = person("income_tax_pre_charges", period)
        other_reductions = add(person, period, ["capped_mcad", "other_tax_credits"])
        return max_(0, step_5_tax - other_reductions)
