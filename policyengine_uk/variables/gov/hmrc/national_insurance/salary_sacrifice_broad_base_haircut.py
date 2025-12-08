from policyengine_uk.model_api import *


class salary_sacrifice_broad_base_haircut(Variable):
    label = "Salary sacrifice broad-base employment income haircut"
    documentation = (
        "Reduction in employment income for ALL workers due to employers spreading "
        "the increased NI costs from the salary sacrifice cap across all employees. "
        "This is a negative value that reduces employment_income. "
        "\n\n"
        "When the salary sacrifice cap is active, employers face increased NI costs "
        "on excess contributions. They spread these costs across ALL employees (not "
        "just salary sacrificers), as they cannot target only affected workers without "
        "those workers negotiating to recoup the loss. "
        "\n\n"
        "See https://policyengine.org/uk/research/uk-salary-sacrifice-cap for methodology."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/uk-salary-sacrifice-cap"

    def formula(person, period, parameters):
        cap = parameters(
            period
        ).gov.hmrc.national_insurance.salary_sacrifice_pension_cap

        # If cap is infinite, no haircut applies
        if np.isinf(cap):
            return 0

        # Get the broad-base haircut rate (applies to ALL workers)
        haircut_rate = parameters(
            period
        ).gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate

        # Apply haircut to employment income before any salary sacrifice adjustments
        # Use employment_income_before_lsr to avoid circular dependency
        employment_income = person("employment_income_before_lsr", period)

        # Return negative value (this reduces employment income for everyone)
        return -employment_income * haircut_rate
