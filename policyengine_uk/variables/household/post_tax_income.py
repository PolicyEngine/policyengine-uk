from policyengine_uk.model_api import *


class post_tax_income(Variable):
    label = "post-tax income"
    documentation = (
        "The household sum of gross_taxable_inputs less Income Tax and "
        "National Insurance. This historical household measure retains "
        "its input base, including its exclusion of statutory pay, rather "
        "than using the statutory Income Tax definition of total income."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["gross_taxable_inputs"]
    subtracts = ["income_tax", "national_insurance"]
