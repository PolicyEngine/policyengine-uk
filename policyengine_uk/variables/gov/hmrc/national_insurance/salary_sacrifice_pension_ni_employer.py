from policyengine_uk.model_api import *


class salary_sacrifice_pension_ni_employer(Variable):
    label = "Employer NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employer National Insurance contributions due to "
        "salary sacrifice pension contributions exceeding the cap. "
        "The excess (after employer haircut) is redirected to regular "
        "pension contributions and subject to employer NI."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/salary-sacrifice-cap"

    def formula(person, period, parameters):
        # Get the excess that's redirected to regular pension (after haircut)
        # This is the amount subject to employer NI
        excess_after_haircut = person(
            "salary_sacrifice_returned_to_income", period
        )

        # Use existing NI Class 1 employer rate parameter
        ni_params = parameters(period).gov.hmrc.national_insurance.class_1
        employer_rate = ni_params.rates.employer

        return excess_after_haircut * employer_rate
