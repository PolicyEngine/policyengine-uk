from policyengine_uk.model_api import *


class salary_sacrifice_broad_base_haircut(Variable):
    label = "Salary sacrifice broad-base employment income haircut"
    documentation = (
        "Reduction in employment income for ALL workers due to employers spreading "
        "the increased NI costs from the salary sacrifice cap across all employees. "
        "This is a negative value that reduces employment_income. "
        "\n\n"
        "When the salary sacrifice cap is active, employers face increased NI costs "
        "on excess contributions. They spread these costs across ALL employees (not "
        "just salary sacrificers), as they cannot target only affected workers without "
        "those workers negotiating to recoup the loss. "
        "\n\n"
        "See https://policyengine.org/uk/research/uk-salary-sacrifice-cap for methodology. "
        "\n\n"
        "By default, this returns 0 (no haircut). To apply a haircut, use the "
        "salary_sacrifice_haircut reform from policyengine_uk.reforms.policyengine."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/uk-salary-sacrifice-cap"

    def formula(person, period, parameters):
        # By default, no haircut applies.
        # Use salary_sacrifice_haircut reform to apply a haircut rate.
        return 0
