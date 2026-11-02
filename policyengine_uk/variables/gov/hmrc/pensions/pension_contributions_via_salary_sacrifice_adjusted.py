from policyengine_uk.model_api import *


class pension_contributions_via_salary_sacrifice_adjusted(Variable):
    label = "Adjusted salary sacrifice pension contributions (capped)"
    documentation = (
        "The NIC-exempt amount of salary sacrifice pension contributions after "
        "counting them only for people with pay and applying the cap. "
        "Contributions above the cap remain employer pension contributions, "
        "but are subject to NICs through salary_sacrifice_pension_ni_excess."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/salary-sacrifice-cap"

    def formula(person, period, parameters):
        intended_ss = person(
            "pension_contributions_via_salary_sacrifice_from_pay", period
        )
        cap = parameters(
            period
        ).gov.hmrc.national_insurance.salary_sacrifice_pension_cap

        # If cap is infinite, no adjustment needed
        if np.isinf(cap):
            return intended_ss

        # Cap the salary sacrifice at the limit
        # The excess is separately included in NIC earnings only.
        return min_(intended_ss, cap)
