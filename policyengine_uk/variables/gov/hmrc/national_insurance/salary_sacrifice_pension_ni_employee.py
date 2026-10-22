from policyengine_uk.model_api import *


class salary_sacrifice_pension_ni_employee(Variable):
    label = "Employee NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employee National Insurance contributions due to "
        "salary sacrifice pension contributions exceeding the cap. "
        "The excess remains an employer pension contribution and is included "
        "only in NIC earnings. This reporting approximation is separate "
        "from the actual Class 1 contribution curves and liability flags."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/uk-salary-sacrifice-cap"

    def formula(person, period, parameters):
        # NIC-only earnings; this does not become an actual member payment.
        excess = person("salary_sacrifice_pension_ni_excess", period)

        # Use existing NI Class 1 parameters
        ni_params = parameters(period).gov.hmrc.national_insurance.class_1
        employment_income = person("employment_income", period)
        upper_earnings_limit = (
            ni_params.employee_scale.components[2].threshold * WEEKS_IN_YEAR
        )

        # Apply appropriate NI rate based on income level
        # Main rate (8%) for income <= UEL, additional rate (2%) for income > UEL
        ni_rate = where(
            employment_income <= upper_earnings_limit,
            ni_params.employee_scale.components[1].rate,
            ni_params.employee_scale.components[2].rate,
        )

        return excess * ni_rate
