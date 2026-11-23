from policyengine_uk.model_api import *


class firm_disposal_proceeds_full_expensing(Variable):
    value_type = float
    entity = Firm
    label = "Firm disposal proceeds of fully expensed main-rate plant"
    documentation = (
        "The part of the main pool disposal proceeds "
        "(firm_disposal_proceeds_main_pool) that relates to new main-rate "
        "plant and machinery on which the company claimed full expensing "
        "under section 45S of the Capital Allowances Act 2001: the disposal "
        "value times the relevant proportion, which is 1 where the whole cost "
        "was fully expensed. It is included in, not added to, the main pool "
        "disposal proceeds. A company is charged on it in full as a balancing "
        "charge, and the pool's disposal receipts are reduced by the same "
        "amount (section 59A). Disposals of special-rate plant that had the "
        "50% section 45S allowance (section 59B) and of plant that had the "
        "super-deduction are not modelled."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = 0
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/59A",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/45S",
    )
