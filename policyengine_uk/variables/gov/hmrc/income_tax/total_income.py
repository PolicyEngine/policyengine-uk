from policyengine_uk.model_api import *


class total_income(Variable):
    """ITA 2007 s.23 Step 1: "amounts of income on which the taxpayer is
    charged to income tax". Section 989 applies this meaning throughout the
    Income Tax Acts ("see Step 1 in that section and also section 31").
    Section 31 treats income subject to deduction at source as "income of
    that tax year"; inputs represent that year's gross amounts, not receipts
    after withholding.
    """

    value_type = float
    entity = Person
    label = "Total income before Income Tax Step 2 reliefs"
    documentation = (
        "Income Tax Act 2007 s.23 Step 1 total income, before Step 2 reliefs "
        "and personal allowances. Delegates to total_income_charged_to_tax, "
        "which sums adjusted_net_income_components (plus basic income when "
        "a reform taxes it), restores the carried-"
        "forward trading loss relief deducted inside those components, and "
        "deducts net-pay pension relief held separately by the tax model. "
        "The component definitions and their documented limitations apply; "
        "in particular miscellaneous income is already net of any same-"
        "source loss and dividend income of modelled deficiency relief. "
        "Statutory sick, maternity and paternity pay enter once through "
        "taxable_employment_income. Household post-tax income and basic "
        "income phase-outs use the separate gross_taxable_inputs base."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/31",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/989",
    ]
    unit = GBP

    # Preserve the exported variable and its non-empty adds metadata.
    adds = ["total_income_charged_to_tax"]
