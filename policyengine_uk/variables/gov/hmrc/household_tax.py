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
        "wealth_tax",
        "non_primary_residence_wealth_tax",
        "income_tax",
        "national_insurance",
        "LVT",
        "carbon_tax",
        "vat_change",
        "capital_gains_tax",
        "private_school_vat",
        "corporate_incident_tax_revenue_change",
        "consumer_incident_tax_revenue_change",
        "high_income_incident_tax_change",
        "employer_ni_response_capital_incidence",
        "employer_ni_response_consumer_incidence",
        "student_loan_repayments",
    ]

    def formula(household, period, parameters):
        if parameters(period).gov.contrib.abolish_council_tax:
            return add(
                household,
                period,
                [
                    tax
                    for tax in household_tax.adds
                    if tax not in ["council_tax"]
                ],
            )
        else:
            return add(household, period, household_tax.adds)
