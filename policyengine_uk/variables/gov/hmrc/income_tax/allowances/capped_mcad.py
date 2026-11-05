from policyengine_uk.model_api import *


class capped_mcad(Variable):
    label = "capped Married Couples' Allowance deduction"
    documentation = (
        "The married couple's allowance tax reduction deducted at Step 6 of "
        "the Income Tax calculation. It is limited to the tax calculated at "
        "Step 5 left after the reductions in other_tax_credits, which hold the "
        "VCT, EIS, SEIS, social investment, community investment and "
        "maintenance reductions deducted before it. It never reduces the "
        "charges added at Step 7, such as the High Income Child Benefit "
        "Charge. Foreign tax relief, also in other_tax_credits, should be "
        "deducted after it (s. 27(6)); the order changes how the total is "
        "split between the reductions, not the total."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        dict(
            title="Income Tax Act 2007 s. 27(4) and (5)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/27",
        ),
        dict(
            title="Income Tax Act 2007 s. 29(2) and (3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
    ]

    def formula(person, period, parameters):
        tax_left = max_(
            0,
            person("income_tax_pre_charges", period)
            - person("other_tax_credits", period),
        )
        return min_(person("married_couples_allowance_deduction", period), tax_left)
