from policyengine_uk.model_api import *


class tax(Variable):
    value_type = float
    entity = Person
    label = "Taxes"
    definition_period = YEAR
    unit = GBP

    adds = ["income_tax", "national_insurance"]


class household_tax(Variable):
    value_type = float
    entity = Household
    label = "taxes"
    documentation = "Total taxes owed by the household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "change_in_expected_sdlt",
        "change_in_expected_ltt",
        "change_in_expected_lbtt",
        "corporate_sdlt_change_incidence",
        "business_rates_change_incidence",
        "council_tax",
        "domestic_rates",
        "change_in_fuel_duty",
        "tv_licence",
        "wealth_tax",
        "non_primary_residence_wealth_tax",
        "income_tax",
        "national_insurance",
        "LVT",
        "carbon_tax",
        "vat_change",
    ]

    def formula(household, period, parameters):
        if parameters(period).gov.contrib.abolish_council_tax:
            return add(
                household,
                period,
                [
                    tax
                    for tax in household_tax.adds
                    if tax not in ["council_tax"]
                ],
            )
        else:
            return add(household, period, household_tax.adds)


class benunit_tax(Variable):
    value_type = float
    entity = BenUnit
    label = "Benefit unit tax paid"
    definition_period = YEAR
    unit = GBP

    adds = ["tax"]


class tax_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported tax paid"
    definition_period = YEAR
    unit = GBP


class tax_modelling(Variable):
    value_type = float
    entity = Person
    label = "Difference between reported and imputed tax liabilities"
    definition_period = YEAR
    unit = GBP

    adds = ["tax"]
    subtracts = ["tax_reported"]
