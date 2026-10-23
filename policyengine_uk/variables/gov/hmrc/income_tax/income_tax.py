from policyengine_uk.model_api import *


class income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax"
    documentation = (
        "Total Income Tax liability: the tax calculated at Step 5, less the "
        "tax reductions deducted at Step 6, plus the charges added at Step 7."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax Act 2007 s. 23",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        ),
        dict(
            title="Income Tax Act 2007 s. 29(2)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
        dict(
            title="Income Tax Act 2007 s. 30",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/30",
        ),
    ]
    category = TAX

    def formula(person, period, parameters):
        # Step 6 deducts the tax reductions from the Step 5 tax, and only so far
        # as there is Step 5 tax to deduct them from (ITA 2007 s. 29(2)). Step 7
        # then adds the s. 30 charges to the tax left, so a reduction larger
        # than the Step 5 tax never offsets a charge.
        tax_left_after_step_6 = max_(
            0,
            person("income_tax_pre_charges", period)
            - person("income_tax_reductions", period),
        )
        return tax_left_after_step_6 + person("income_tax_charges", period)
