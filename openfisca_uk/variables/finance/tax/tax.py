from openfisca_uk.model_api import *


class tax(Variable):
    value_type = float
    entity = Person
    label = "Taxes"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        TAXES = ["income_tax", "national_insurance"]
        return add(person, period, TAXES)


class household_tax(Variable):
    value_type = float
    entity = Household
    label = "Taxes"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(household, period):
        personal_taxes = household.sum(household.members("tax", period))
        HOUSEHOLD_TAXES = [
            "expected_sdlt",
            "expected_ltt",
            "expected_lbtt",
            "business_rates",
            "council_tax",
        ]
        household_taxes = add(household, period, HOUSEHOLD_TAXES)
        return personal_taxes + household_taxes


class benunit_tax(Variable):
    value_type = float
    entity = BenUnit
    label = "Benefit unit tax paid"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["tax"])


class tax_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported tax paid"
    definition_period = YEAR
    unit = "currency-GBP"


class tax_modelling(Variable):
    value_type = float
    entity = Person
    label = "Difference between reported and imputed tax liabilities"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("tax", period) - person("tax_reported", period)
