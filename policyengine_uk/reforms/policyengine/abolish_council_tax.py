from policyengine_uk.model_api import *


def create_abolish_council_tax() -> Reform:
    """
    Reform that abolishes council tax by removing it from tax calculations.

    Policy: Remove council tax from gov_tax and household_tax calculations.
    """

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
            # "council_tax",  # Removed in abolish_council_tax reform
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
            # "council_tax",  # Removed in abolish_council_tax reform
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
            "employer_ni_response_capital_incidence",
            "employer_ni_response_consumer_incidence",
            "student_loan_repayments",
        ]

    class reform(Reform):
        def apply(self):
            self.update_variable(gov_tax)
            self.update_variable(household_tax)

    return reform


def create_abolish_council_tax_reform(
    parameters, period, bypass: bool = False
):
    if bypass:
        return create_abolish_council_tax()

    if parameters(period).gov.contrib.abolish_council_tax:
        return create_abolish_council_tax()
    else:
        return None


# For direct import
abolish_council_tax_reform = create_abolish_council_tax()
