from policyengine_uk.model_api import *


class property_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction applied by the property allowance"
    documentation = (
        "Relief from the property allowance beyond the expenses already "
        "deducted in property_income: property_allowance_deduction_if_used "
        "where the person uses the allowance, and nil where they deduct "
        "actual expenses and take the finance-cost tax reduction instead "
        "(uses_property_allowance)."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BD",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BD",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BF (full relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BF",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BH (partial relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BH",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BL",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BL",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        return where(
            person("uses_property_allowance", period),
            person("property_allowance_deduction_if_used", period),
            0,
        )
