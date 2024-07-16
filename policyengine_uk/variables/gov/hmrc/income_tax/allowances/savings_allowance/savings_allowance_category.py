from policyengine_uk.model_api import *

class SavingsAllowanceCategory(Enum):
    ADDITIONAL = "Additional"
    HIGHER = "Higher"
    BASIC = "Basic"

class savings_allowance_category(Variable):
    value_type = str
    entity = Person
    label = "Savings Allowance category for the year"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12B"
    unit = GBP

    def formula(person, period, parameters):
        tax_band = person("tax_band", period)
        tax_bands = tax_band.possible_values
        amounts = parameters(
            period
        ).gov.hmrc.income_tax.allowances.personal_savings_allowance

        is_lowest_bands = (
            (tax_band == tax_bands.STARTER)
            | (tax_band == tax_bands.BASIC)
            | (tax_band == tax_bands.INTERMEDIATE)
        )

        return select(
            [
                tax_band == tax_bands.ADDITIONAL,
                tax_band == tax_bands.HIGHER,
                is_lowest_bands,
                tax_band == tax_bands.NONE,
            ],
            [
                SavingsAllowanceCategory.ADDITIONAL, 
                SavingsAllowanceCategory.HIGHER, 
                SavingsAllowanceCategory.BASIC, 
                SavingsAllowanceCategory.BASIC
            ],
        )