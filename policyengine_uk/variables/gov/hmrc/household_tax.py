from policyengine_uk.model_api import *


class household_tax(Variable):
    value_type = float
    entity = Household
    label = "household taxes"
    documentation = "Total taxes owed by the household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "expected_sdlt",
        "expected_ltt",
        "expected_lbtt",
        "corporate_sdlt",
        "business_rates",
        "council_tax",
        "domestic_rates",
        "fuel_duty",
        "tv_licence",
        # wealth_tax, non_primary_residence_wealth_tax, LVT, carbon_tax
        # excluded - added via contrib_taxes reform
        "income_tax",
        "national_insurance",
        "vat_change",
        "capital_gains_tax",
        "private_school_vat",
        "corporate_incident_tax_revenue_change",
        "consumer_incident_tax_revenue_change",
        "employer_ni_response_capital_incidence",
        "employer_ni_response_consumer_incidence",
        "student_loan_repayments",
    ]
