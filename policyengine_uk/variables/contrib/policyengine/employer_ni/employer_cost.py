from policyengine_uk.model_api import *


class employer_cost(Variable):
    label = "employer cost"
    documentation = (
        "Pay, statutory sick, maternity and paternity pay, employer pension "
        "contributions and employer National Insurance: secondary Class 1 "
        "and Class 1A. The cost excludes the tax valuation of the benefits "
        "in kind themselves. The employer NI incidence formulas hold this "
        "modeled cost subject to the cash-pay floor and incidence assumptions."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        benefits = add(
            person,
            period,
            [
                "statutory_sick_pay",
                "statutory_maternity_pay",
                "statutory_paternity_pay",
            ],
        )
        return (
            person("employment_income", period)
            + person("ni_employer", period)
            + person("employer_pension_contributions", period)
            + benefits
        )
