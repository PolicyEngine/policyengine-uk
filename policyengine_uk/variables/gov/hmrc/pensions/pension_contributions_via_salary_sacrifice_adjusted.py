from policyengine_uk.model_api import *


class pension_contributions_via_salary_sacrifice_adjusted(Variable):
    label = "Adjusted salary sacrifice pension contributions after behavioral response"
    documentation = (
        "The actual amount of salary sacrifice pension contributions after employees "
        "adjust their behavior in response to the salary sacrifice cap. When the cap "
        "is active and employees face NI charges on excess contributions, they may "
        "reduce their salary sacrifice to the cap level. The reduction rate is "
        "controlled by the employee_salary_sacrifice_reduction_rate parameter."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://docs.google.com/document/d/1Rhrfrg7A_oZHudmA775otAn1EE4-YthgeyS9nL-PrE8/edit?tab=t.0"

    def formula(person, period, parameters):
        intended_ss = person(
            "pension_contributions_via_salary_sacrifice", period
        )
        cap = parameters(
            period
        ).gov.hmrc.national_insurance.salary_sacrifice_pension_cap

        # If cap is infinite, no adjustment needed
        if np.isinf(cap):
            return intended_ss

        # Calculate excess above cap
        excess = max_(intended_ss - cap, 0)

        # Get behavioral response rate
        reduction_rate = parameters(
            period
        ).gov.contrib.behavioral_responses.employee_salary_sacrifice_reduction_rate

        # Amount employee reduces their salary sacrifice
        reduction = excess * reduction_rate

        # Adjusted salary sacrifice (cannot go below zero)
        return max_(intended_ss - reduction, 0)
