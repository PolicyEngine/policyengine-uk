from policyengine_uk.model_api import *


class firm_only_tax(Variable):
    label = "Firm-only tax liability"
    documentation = (
        "The part of a firm's tax liability set by rules that only the firm "
        "side models, so that a reform to them reaches households through "
        "firm_tax_incidence without counting a change twice: corporation "
        "tax, the bank surcharge, the apprenticeship levy, business rates, "
        "Class 1A on termination awards, Class 1B, the soft drinks industry "
        "levy, the plastic packaging tax, the residential property developer "
        "tax, the digital services tax and the energy profits levy, less R&D tax credits paid out "
        "to the firm. Class 1A on termination awards and Class 1B have no "
        "household-side counterpart, so they belong here. Off-payroll "
        "secondary Class 1 and Class 1A on benefits in kind are left out "
        "with the rest of employer National Insurance. Employer National Insurance rates and thresholds, and VAT "
        "rates, reach households through ni_employer and vat on the "
        "household side, so they are left out. The Employment Allowance is "
        "left out too: firm_tax_change_total subtracts its full change, "
        "which with the gross change in ni_employer counts the change in "
        "what firms pay. firm_tax_change_total also adds the change in firm "
        "VAT from VAT rules other than the rates, with the rates held at "
        "baseline."
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
        "firm_termination_award_class_1a_ni",
        "firm_class_1b_ni",
        "soft_drinks_industry_levy",
        "plastic_packaging_tax",
        "residential_property_developer_tax",
        "digital_services_tax",
        "energy_profits_levy",
    ]
    subtracts = ["firm_rdec_excess_payable", "firm_rd_payable_credit"]
