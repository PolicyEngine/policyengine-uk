from policyengine_uk.model_api import *


def create_salary_sacrifice_haircut() -> Reform:
    """
    Reform that applies a broad-base haircut to all workers' employment income
    due to employers spreading salary sacrifice cap costs.

    Policy: When the salary sacrifice cap is active, employers face increased NI
    costs on excess contributions. They spread these costs across ALL employees
    (not just salary sacrificers), as they cannot target only affected workers
    without those workers negotiating to recoup the loss.

    The haircut rate is read from parameters at calculation time, allowing
    dynamic configuration through YAML tests or API calls.
    """

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
        reference = (
            "https://policyengine.org/uk/research/uk-salary-sacrifice-cap"
        )

        def formula(person, period, parameters):
            cap = parameters(
                period
            ).gov.hmrc.national_insurance.salary_sacrifice_pension_cap

            # If cap is infinite, no haircut applies
            if np.isinf(cap):
                return 0

            # Get haircut rate from parameters at calculation time
            haircut_rate = parameters(
                period
            ).gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate

            # If no haircut rate set, return 0
            if haircut_rate == 0:
                return 0

            # Apply haircut to employment income before any salary sacrifice adjustments
            # Use employment_income_before_lsr to avoid circular dependency
            employment_income = person("employment_income_before_lsr", period)

            # Return negative value (this reduces employment income for everyone)
            return -employment_income * haircut_rate

    class reform(Reform):
        def apply(self):
            self.update_variable(salary_sacrifice_broad_base_haircut)

    return reform


def create_salary_sacrifice_haircut_reform(
    parameters, period, bypass: bool = False
):
    """
    Factory function to create the salary sacrifice haircut reform.

    This reform is ALWAYS applied because the formula checks parameters at
    calculation time. This allows dynamic parameter setting (e.g., in YAML tests
    or API calls) to work correctly.

    Args:
        parameters: The parameter tree (unused, kept for API consistency)
        period: The time period (unused, kept for API consistency)
        bypass: If True, always create the reform (always True here)

    Returns:
        A Reform class
    """
    # Always apply this reform - the formula checks parameters internally
    # This matches the US pattern where reforms are always active but
    # their effect depends on parameter values at calculation time
    return create_salary_sacrifice_haircut()


# For direct import
salary_sacrifice_haircut_reform = create_salary_sacrifice_haircut()
