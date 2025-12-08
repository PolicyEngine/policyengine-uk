from policyengine_uk.model_api import *


class salary_sacrifice_returned_to_income(Variable):
    label = "Amount of salary sacrifice redirected to employee pension contributions"
    documentation = (
        "The amount of excess salary sacrifice (above the cap) that is redirected "
        "to regular employee pension contributions. This maintains total pension savings "
        "while subjecting the excess to National Insurance (but not income tax, since "
        "regular pension contributions receive income tax relief). "
        "\n\n"
        "The full excess is redirected - the employer cost increase is handled via "
        "the broad-base haircut (salary_sacrifice_broad_base_haircut) which reduces "
        "ALL workers' employment income by ~0.16%, not just affected workers."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/uk-salary-sacrifice-cap"

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

        # Calculate excess above cap - full excess is redirected to regular
        # employee pension contributions (no targeted haircut on the individual)
        excess = max_(intended_ss - cap, 0)

        # Full excess is redirected to employment income (and then to employee
        # pension contributions for income tax relief). The employer NI cost
        # increase is spread across ALL workers via salary_sacrifice_broad_base_haircut.
        return excess
