from policyengine_uk.model_api import *


class employer_pension_reduction_from_ss_cap(Variable):
    label = (
        "Employer pension contribution reduction due to salary sacrifice cap"
    )
    documentation = """
    Behavioral response: Amount by which employers reduce their pension
    contributions in response to the additional NI charge from the salary
    sacrifice pension cap.

    This models the real-world behavior where employers offset the 15% NI
    charge by reducing the pension contributions they make on behalf of employees.

    The reduction percentage is controlled by the
    'employer_pension_reduction_rate' parameter:
    - 0% = employers absorb full cost (no reduction)
    - 50% = employers reduce contributions by half the NI charge
    - 100% = employers fully offset the NI charge
    """
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.ft.com/content/11602ac1-44fc-4b58-8b17-af5e851f5c95"
    )

    def formula(person, period, parameters):
        # Calculate the employer NI charge from salary sacrifice cap
        employer_ni_charge = person(
            "salary_sacrifice_pension_ni_employer", period
        )

        # Get the behavioral response rate parameter
        reduction_rate = parameters(
            period
        ).gov.contrib.behavioral_responses.employer_pension_reduction_rate

        # Employers reduce pension contributions to offset NI costs
        return employer_ni_charge * reduction_rate
