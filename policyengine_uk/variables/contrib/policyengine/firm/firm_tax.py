from policyengine_uk.model_api import *


class firm_tax(Variable):
    label = "Firm tax liability"
    documentation = (
        "The firm's statutory liability to the firm-side taxes this model "
        "covers: corporation tax, the bank surcharge, the apprenticeship "
        "levy, employer National Insurance (secondary Class 1 after the Employment Allowance, "
        "off-payroll secondary Class 1, Class 1A on benefits in kind and on "
        "termination awards, and Class 1B), business rates, VAT, the soft "
        "drinks industry levy, the plastic packaging tax, the residential "
        "property developer tax, the digital services tax and the energy "
        "profits levy, less R&D tax credits paid out to the firm "
        "(R&D expenditure credit above its corporation tax, and the payable "
        "credit for loss-making SMEs: every SME claiming the SME scheme "
        "before April 2024, and R&D-intensive SMEs from then). This is liability, not "
        "incidence: summed "
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
        "firm_class_1a_ni",
        "firm_off_payroll_employer_ni",
        "firm_termination_award_class_1a_ni",
        "firm_class_1b_ni",
        "firm_business_rates",
        "soft_drinks_industry_levy",
        "plastic_packaging_tax",
        "residential_property_developer_tax",
        "digital_services_tax",
        "energy_profits_levy",
        "firm_vat",
    ]
    subtracts = ["firm_rdec_excess_payable", "firm_rd_payable_credit"]
