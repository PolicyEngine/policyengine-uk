from policyengine_uk.model_api import *


class firm_tax(Variable):
    label = "Firm tax liability"
    documentation = (
        "The firm's statutory liability to the firm-side taxes this model "
        "covers: corporation tax, the bank surcharge, the apprenticeship "
        "levy, employer National Insurance (after the Employment Allowance), "
        "business rates and VAT. This is liability, not incidence: summed "
        "over firms with firm_weight it is a receipts measure that must not "
        "be added to gov_tax, whose household terms already include employer "
        "National Insurance, VAT and business rates as incidence."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "corporation_tax",
        "bank_surcharge",
        "apprenticeship_levy",
        "firm_employer_ni",
        "firm_business_rates",
        "firm_vat",
    ]
