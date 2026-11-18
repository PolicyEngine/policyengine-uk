from policyengine_uk.model_api import *


class guardians_allowance_full_rate_child_weeks(Variable):
    value_type = float
    entity = Person
    label = "Full-rate Guardian's Allowance child-weeks"
    documentation = (
        "Source-qualified nonnegative full-rate payable child-weeks for "
        "this legal holder, valued at the represented tax year's annualised "
        "weekly rate. A steady one-child 52-week reference is 52; two such "
        "children are 104. The supplied exposure establishes full-rate "
        "payability as well as the relevant entitlement conditions; the "
        "model does not infer it from household relationships. Mixed-rate, "
        "prison-adjusted, frozen-abroad and other exceptional payments need "
        "authoritative direct cash instead. This is not an exact weekly "
        "payment ledger or an automatic claim-backdating calculation."
    )
    definition_period = YEAR
    default_value = 0
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/77",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/77",
        "https://www.legislation.gov.uk/uksi/2003/495/regulation/8",
    )
