from policyengine_uk.model_api import *


class salary_sacrifice_pension_ni_employer(Variable):
    label = "Employer NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employer National Insurance contributions due to "
        "salary sacrifice pension contributions exceeding the £2,000 cap. "
        "The excess is subject to the standard employer NI rate of 15%."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.ft.com/content/11602ac1-44fc-4b58-8b17-af5e851f5c95"
    )

    def formula(person, period, parameters):
        # Check if reform is in effect
        reform_in_effect = parameters(
            period
        ).gov.contrib.salary_sacrifice_pension_cap_in_effect
        if not reform_in_effect:
            return 0

        ss_contributions = person(
            "pension_contributions_via_salary_sacrifice", period
        )
        cap = parameters(
            period
        ).gov.hmrc.national_insurance.salary_sacrifice_pension_cap
        excess = max_(ss_contributions - cap, 0)

        # Use existing NI Class 1 employer rate parameter
        ni_params = parameters(period).gov.hmrc.national_insurance.class_1
        employer_rate = ni_params.rates.employer

        return excess * employer_rate
