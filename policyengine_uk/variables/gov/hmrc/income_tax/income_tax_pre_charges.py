from policyengine_uk.model_api import *


class income_tax_pre_charges(Variable):
    value_type = float
    entity = Person
    label = "Income Tax before any tax charges"
    documentation = (
        "The tax calculated at Step 5 of the Income Tax calculation: the tax "
        "at each rate on the parts of income left after allowances, added "
        "together. Tax reductions are deducted from it at Step 6, and only so "
        "far as it is enough to deduct them from."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )
    unit = GBP

    adds = "gov.hmrc.income_tax.step_5_tax_components"
