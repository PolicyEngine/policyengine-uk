from policyengine_uk.model_api import *


class salary_sacrifice_returned_to_income(Variable):
    label = "Amount of salary sacrifice redirected to employee pension contributions"
    documentation = (
        "The amount of excess salary sacrifice (above the cap) that is redirected "
        "to regular employee pension contributions. This maintains total pension savings "
        "while subjecting the excess to National Insurance (but not income tax, since "
        "regular pension contributions receive income tax relief). An employer haircut is "
        "applied to reflect employers spreading increased NI costs across workers."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/salary-sacrifice-cap"

    def formula(person, period, parameters):
        intended_ss = person(
            "pension_contributions_via_salary_sacrifice", period
        )
        cap = parameters(
            period
        ).gov.hmrc.national_insurance.salary_sacrifice_pension_cap

        # If cap is infinite, no excess to redirect
        if np.isinf(cap):
            return 0

        # Calculate raw excess above cap (no behavioral response - employees redirect all excess)
        excess = max_(intended_ss - cap, 0)

        # Apply employer haircut (employers spread NI costs across workers)
        haircut = parameters(
            period
        ).gov.contrib.behavioral_responses.employer_salary_sacrifice_haircut

        # Return excess minus haircut (redirected to employee pension contributions)
        # This amount:
        # 1. Gets added to employee_pension_contributions (income tax relief)
        # 2. Is subject to NI (no NI relief like salary sacrifice)
        return excess * (1 - haircut)
