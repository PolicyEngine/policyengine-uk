from policyengine_uk.model_api import *


GOV_TAX_VARIABLES = [
    "expected_sdlt",
    "expected_ltt",
    "expected_lbtt",
    "corporate_sdlt",
    "business_rates",
    "council_tax",
    "high_value_council_tax_surcharge",
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
    "ni_employer",
    "student_loan_repayments",
    "vat",
]


class gov_tax(Variable):
    label = "government tax revenue"
    documentation = "Government tax revenue impact in respect of this household."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        variables = list(GOV_TAX_VARIABLES)
        abolish_council_tax = parameters.gov.contrib.abolish_council_tax(period)
        if abolish_council_tax:
            variables = [
                variable
                for variable in variables
                if variable not in ["council_tax", "high_value_council_tax_surcharge"]
            ]

        return add(household, period, variables)
