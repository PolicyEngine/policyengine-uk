from policyengine_uk.model_api import *


class employee_pension_contributions(Variable):
    label = "employee pension contributions (reported)"
    documentation = "Employee pension contributions as reported in survey data"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"


class employee_pension_contributions_adjusted(Variable):
    label = "employee pension contributions (adjusted)"
    documentation = "Total employee pension contributions including adjustments for salary sacrifice cap reforms"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        # Get the base employee pension contributions from input/survey data
        base_contributions = person("employee_pension_contributions", period)

        # Add any salary sacrifice amounts that were returned to income due to cap
        salary_sacrifice_returned = person(
            "salary_sacrifice_returned_to_income", period
        )

        return base_contributions + salary_sacrifice_returned
