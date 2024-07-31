from policyengine_uk.model_api import *


class pension_wealth(Variable):
    label = "pension wealth"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(person, period, parameters):
        if person.has_any_input("pension_wealth"):
            pension_last_year = person("pension_wealth", period.last_year)
            assumed_growth = (
                parameters.gov.obr.non_labour_income.relative_change(
                    period.last_year.start, period.start
                )
            )
            employee_pension_contributions_last_year = person(
                "employee_pension_contributions", period.last_year
            )
            employer_pension_contributions_last_year = person(
                "employer_pension_contributions", period.last_year
            )
            private_pension_contributions_last_year = person(
                "private_pension_contributions", period.last_year
            )
            return (
                pension_last_year * assumed_growth
                + employee_pension_contributions_last_year
                + employer_pension_contributions_last_year
                + private_pension_contributions_last_year
            )


class employee_pension_contributions(Variable):
    label = "employee pension contributions"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


class employer_pension_contributions(Variable):
    label = "employer pension contributions"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


class private_pension_contributions(Variable):
    label = "private pension contributions"
    documentation = (
        "pension contributes made by this person, separately from employment."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
