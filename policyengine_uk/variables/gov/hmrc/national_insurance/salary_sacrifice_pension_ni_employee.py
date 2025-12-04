from policyengine_uk.model_api import *


class salary_sacrifice_pension_ni_employee(Variable):
    label = "Employee NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employee National Insurance contributions due to "
        "salary sacrifice pension contributions exceeding the cap. "
        "The full excess is redirected to regular pension contributions "
        "and subject to NI (but gets income tax relief)."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/uk-salary-sacrifice-cap"

    def formula(person, period, parameters):
        # Get the excess that's redirected to regular pension
        # This is the amount subject to NI
        excess = person("salary_sacrifice_returned_to_income", period)

        # Use existing NI Class 1 parameters
        ni_params = parameters(period).gov.hmrc.national_insurance.class_1
        employment_income = person("employment_income", period)
        upper_earnings_limit = (
            ni_params.thresholds.upper_earnings_limit * WEEKS_IN_YEAR
        )

        # Apply appropriate NI rate based on income level
        # Main rate (8%) for income <= UEL, additional rate (2%) for income > UEL
        ni_rate = where(
            employment_income <= upper_earnings_limit,
            ni_params.rates.employee.main,
            ni_params.rates.employee.additional,
        )

        return excess * ni_rate
