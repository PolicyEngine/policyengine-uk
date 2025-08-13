from policyengine_uk.model_api import *


class gov_tax(Variable):
    label = "government tax revenue"
    documentation = (
        "Government tax revenue impact in respect of this household."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
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
        "capital_gains_tax",
        "private_school_vat",
        "corporate_incident_tax_revenue_change",
        "consumer_incident_tax_revenue_change",
        "high_income_incident_tax_change",
        "ni_employer",
        "student_loan_repayments",
        "vat",
    ]

    def formula(household, period, parameters):
        variables = list(gov_tax.adds)
        if parameters(period).gov.contrib.abolish_council_tax:
            variables = [
                variable for variable in variables if variable != "council_tax"
            ]

        return add(household, period, variables)
