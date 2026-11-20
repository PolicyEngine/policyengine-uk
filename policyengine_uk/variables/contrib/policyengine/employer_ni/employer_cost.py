from policyengine_uk.model_api import *


class employer_cost(Variable):
    label = "employer cost"
    documentation = (
        "Pay, statutory sick, maternity and paternity pay, employer pension "
        "contributions and the secondary Class 1 contributions on them. "
        "Benefits in kind and the Class 1A contributions on them are left "
        "out, as baseline_employer_cost and adjusted_employer_cost leave "
        "them out, so a fixed-employer-cost response to an employer NI "
        "reform holds this cost."
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
            + person("ni_class_1_employer", period)
            + person("employer_pension_contributions", period)
            + benefits
        )
