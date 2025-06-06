from policyengine_uk.model_api import *


class savings_allowance(Variable):
    value_type = float
    entity = Person
    label = "Savings Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12B"
    unit = GBP

    def formula(person, period, parameters):
        tax_band = person("tax_band", period)
        tax_bands = tax_band.possible_values
        amounts = parameters(
            period
        ).gov.hmrc.income_tax.allowances.personal_savings_allowance
        return select(
            [
                tax_band == tax_bands.ADDITIONAL,
                tax_band == tax_bands.HIGHER,
                (
                    (tax_band == tax_bands.STARTER)
                    | (tax_band == tax_bands.BASIC)
                    | (tax_band == tax_bands.INTERMEDIATE)
                ),
                tax_band == tax_bands.NONE,
            ],
            [amounts.additional, amounts.higher, amounts.basic, amounts.basic],
        )
