from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class weekly_rent(Variable):
    value_type = float
    entity = Household
    label = u"Weekly average rent"
    definition_period = YEAR


class rent(Variable):
    value_type = float
    entity = Household
    label = u"Gross rent for the household"
    definition_period = YEAR


@uprated(by="CPI")
class benunit_rent(Variable):
    value_type = float
    entity = BenUnit
    label = u"Rent"
    documentation = "Gross rent that members of this family are liable for"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("personal_rent", period))


class personal_rent(Variable):
    value_type = float
    entity = Person
    label = u"Rent liable"
    documentation = "The gross rent this person is liable for"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.household("rent", period) * person(
            "is_household_head", period
        )


class family_rent(Variable):
    value_type = float
    entity = BenUnit
    label = u"Gross rent for the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        personal_rent = benunit.members("personal_rent", period)
        return benunit.sum(personal_rent)


class childcare_expenses(Variable):
    value_type = float
    entity = Person
    label = u"Cost of childcare"
    definition_period = YEAR


class private_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = u"Private pension contributions"
    definition_period = YEAR


class occupational_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = u"Occupational pension contributions"
    definition_period = YEAR


class housing_service_charges(Variable):
    value_type = float
    entity = Household
    label = u"Housing service charges"
    definition_period = YEAR


class water_and_sewerage_charges(Variable):
    value_type = float
    entity = Household
    label = u"Water and sewerage charges"
    definition_period = YEAR


class employer_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = u"Employer pension contributions"
    definition_period = YEAR


class weekly_childcare_expenses(Variable):
    value_type = float
    entity = Person
    label = u"Average cost of childcare"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("childcare_expenses", period) / WEEKS_IN_YEAR


@uprated(by="CPI")
class housing_costs(Variable):
    value_type = float
    entity = Household
    label = u"Total housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("rent", period) + household("mortgage", period)


class maintenance_expenses(Variable):
    value_type = float
    entity = Person
    label = u"Maintenance expenses"
    definition_period = YEAR


class mortgage_interest_repayment(Variable):
    value_type = float
    entity = Household
    label = u"Total mortgage payments"
    definition_period = YEAR


class mortgage_capital_repayment(Variable):
    value_type = float
    entity = Household
    label = u"Mortgage payments"
    definition_period = YEAR


class mortgage(Variable):
    value_type = float
    entity = Household
    label = u"Total mortgage payments"
    definition_period = YEAR


@uprated(by="council_tax")
class council_tax(Variable):
    value_type = float
    entity = Household
    label = u"Council Tax"
    definition_period = YEAR


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
    label = u"Council Tax Band"
    definition_period = YEAR
