from policyengine_uk.model_api import *


class firm_only_tax(Variable):
    label = "Firm-only tax liability"
    documentation = (
        "The part of a firm's tax liability set by rules that only the firm "
        "side models, so that a reform to them reaches households through "
        "firm_tax_incidence without counting a change twice: corporation "
        "tax, the bank surcharge, the apprenticeship levy and business "
        "rates, less R&D tax credits paid out to the firm. Employer National Insurance rates and thresholds, and VAT "
        "rates, reach households through ni_employer and vat on the "
        "household side, so they are left out. The Employment Allowance is "
        "left out too: firm_tax_change_total subtracts its full change, "
        "which with the gross change in ni_employer counts the change in "
        "what firms pay. Reforms to the VAT registration threshold and flat "
        "rate scheme are not yet carried to households."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "corporation_tax",
        "bank_surcharge",
        "apprenticeship_levy",
        "firm_business_rates",
    ]
    subtracts = ["firm_rdec_excess_payable", "firm_rd_payable_credit"]
