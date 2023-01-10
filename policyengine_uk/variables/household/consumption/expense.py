from policyengine_uk.model_api import *


class benunit_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Rent"
    documentation = "Gross rent that members of this family are liable for"
    definition_period = YEAR
    unit = GBP

    adds = ["personal_rent"]


class personal_rent(Variable):
    value_type = float
    entity = Person
    label = "Rent liable"
    documentation = "The gross rent this person is liable for"
    definition_period = YEAR
    unit = GBP
    defined_for = "is_household_head"
    adds = ["rent"]


class family_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Gross rent for the family"
    definition_period = YEAR
    unit = GBP

    adds = ["personal_rent"]


class weekly_childcare_expenses(Variable):
    value_type = float
    entity = Person
    label = "Average cost of childcare"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return person("childcare_expenses", period) / WEEKS_IN_YEAR


class housing_costs(Variable):
    value_type = float
    entity = Household
    label = "Total housing costs"
    definition_period = YEAR
    unit = GBP

    adds = ["rent", "mortgage"]


class council_tax_less_benefit(Variable):
    label = "Council Tax (less CTB)"
    documentation = "Council Tax minus the Council Tax Benefit"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        person = household.members
        council_tax_benefit = household.sum(
            person.benunit("council_tax_benefit", period)
            * person("is_benunit_head", period)
        )
        return household("council_tax", period) - council_tax_benefit
