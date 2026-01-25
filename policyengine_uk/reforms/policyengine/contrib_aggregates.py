from policyengine_uk.model_api import *


def create_contrib_aggregates() -> Reform:
    """
    Reform that adds contrib tax/spending variables to gov aggregates.

    This reform adds wealth_tax, non_primary_residence_wealth_tax, LVT,
    carbon_tax, and other_public_spending_budget_change to the appropriate
    gov/ aggregate variables.

    These are contrib (policy proposal) variables that should not be in
    the baseline gov/ variables representing actual law.
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
            "council_tax",
            "domestic_rates",
            "fuel_duty",
            "tv_licence",
            "wealth_tax",
            "non_primary_residence_wealth_tax",
            "LVT",
            "carbon_tax",
            "income_tax",
            "national_insurance",
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
            "council_tax",
            "domestic_rates",
            "fuel_duty",
            "tv_licence",
            "wealth_tax",
            "non_primary_residence_wealth_tax",
            "LVT",
            "carbon_tax",
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

    class gov_spending(Variable):
        label = "government spending"
        documentation = (
            "Government spending impact in respect of this household."
        )
        entity = Household
        definition_period = YEAR
        value_type = float
        unit = GBP
        adds = [
            "child_benefit",
            "esa_income",
            "esa_contrib",
            "housing_benefit",
            "income_support",
            "jsa_income",
            "jsa_contrib",
            "pension_credit",
            "universal_credit",
            "working_tax_credit",
            "child_tax_credit",
            "attendance_allowance",
            "afcs",
            "bsp",
            "carers_allowance",
            "dla",
            "iidb",
            "incapacity_benefit",
            "pip",
            "sda",
            "state_pension",
            "maternity_allowance",
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "ssmg",
            # basic_income added via basic_income_interactions reform
            "epg_subsidy",
            "cost_of_living_support_payment",
            "energy_bills_rebate",
            "winter_fuel_allowance",
            "pawhp",
            "other_public_spending_budget_change",
            "tax_free_childcare",
            "extended_childcare_entitlement",
            "universal_childcare_entitlement",
            "targeted_childcare_entitlement",
            "care_to_learn",
            "dfe_education_spending",
            "dft_subsidy_spending",
            "nhs_spending",
        ]

    class reform(Reform):
        def apply(self):
            self.update_variable(gov_tax)
            self.update_variable(household_tax)
            self.update_variable(gov_spending)

    return reform


def create_contrib_aggregates_reform(parameters, period, bypass: bool = False):
    """
    Creates the contrib aggregates reform.

    This reform is ALWAYS applied because the contrib variables return 0
    by default when their parameters aren't set, so adding them has no
    effect unless the user explicitly enables them.

    Args:
        parameters: The parameter tree (unused, kept for API consistency)
        period: The period (unused, kept for API consistency)
        bypass: If True, return the reform unconditionally (always True here)

    Returns:
        Reform class
    """
    # Always apply this reform - contrib variables return 0 by default
    return create_contrib_aggregates()


# For direct import
contrib_aggregates_reform = create_contrib_aggregates()
