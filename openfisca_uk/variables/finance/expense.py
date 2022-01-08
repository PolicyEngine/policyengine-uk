from openfisca_uk.model_api import *


class weekly_rent(Variable):
    value_type = float
    entity = Household
    label = "Weekly average rent"
    definition_period = YEAR
    unit = "currency-GBP"


@uprated(by="CPI")
class benunit_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Rent"
    documentation = "Gross rent that members of this family are liable for"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["personal_rent"])


class personal_rent(Variable):
    value_type = float
    entity = Person
    label = "Rent liable"
    documentation = "The gross rent this person is liable for"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        rent = person.household("rent", period)
        is_household_head = person("is_household_head", period)
        return rent * is_household_head


class family_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Gross rent for the family"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        personal_rent = benunit.members("personal_rent", period)
        return benunit.sum(personal_rent)


class childcare_expenses(Variable):
    value_type = float
    entity = Person
    label = "Cost of childcare"
    definition_period = YEAR
    unit = "currency-GBP"


class private_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Private pension contributions"
    definition_period = YEAR
    unit = "currency-GBP"


class occupational_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Occupational pension contributions"
    definition_period = YEAR
    unit = "currency-GBP"


class housing_service_charges(Variable):
    value_type = float
    entity = Household
    label = "Housing service charges"
    definition_period = YEAR
    unit = "currency-GBP"


class water_and_sewerage_charges(Variable):
    value_type = float
    entity = Household
    label = "Water and sewerage charges"
    definition_period = YEAR


class employer_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Employer pension contributions"
    definition_period = YEAR
    unit = "currency-GBP"


class weekly_childcare_expenses(Variable):
    value_type = float
    entity = Person
    label = "Average cost of childcare"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("childcare_expenses", period) / WEEKS_IN_YEAR


@uprated(by="CPI")
class housing_costs(Variable):
    value_type = float
    entity = Household
    label = "Total housing costs"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return add(household, period, ["rent", "mortgage"])


class maintenance_expenses(Variable):
    value_type = float
    entity = Person
    label = "Maintenance expenses"
    definition_period = YEAR
    unit = "currency-GBP"


class mortgage_interest_repayment(Variable):
    value_type = float
    entity = Household
    label = "Total mortgage payments"
    definition_period = YEAR
    unit = "currency-GBP"


class mortgage_capital_repayment(Variable):
    value_type = float
    entity = Household
    label = "Mortgage payments"
    definition_period = YEAR
    unit = "currency-GBP"


class mortgage(Variable):
    value_type = float
    entity = Household
    label = "Total mortgage payments"
    definition_period = YEAR
    unit = "currency-GBP"


@uprated(by="council_tax")
class council_tax(Variable):
    value_type = float
    entity = Household
    label = "Council Tax"
    definition_period = YEAR
    unit = "currency-GBP"


class council_tax_less_benefit(Variable):
    label = "Council Tax (less CTB)"
    documentation = "Council Tax minus the Council Tax Benefit"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        person = household.members
        council_tax_benefit = household.sum(
            person.benunit("council_tax_benefit", period)
            * person("is_benunit_head", period)
        )
        return household("council_tax", period) - council_tax_benefit


class CouncilTaxBand(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"


class council_tax_band(Variable):
    value_type = Enum
    possible_values = CouncilTaxBand
    default_value = CouncilTaxBand.D
    entity = Household
    label = "Council Tax Band"
    definition_period = YEAR
