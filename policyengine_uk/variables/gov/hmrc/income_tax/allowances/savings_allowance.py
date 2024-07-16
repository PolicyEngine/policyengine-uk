from policyengine_uk.model_api import *

class savings_allowance(Variable):
    value_type = float
    entity = Person
    label = "Savings Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12B"
    unit = GBP

    def formula(person, period, parameters):
        amounts = parameters(
            period
        ).gov.hmrc.income_tax.allowances.personal_savings_allowance

        savings_allowance_category = person("savings_allowance_category", period)
        max_allowance = amounts[savings_allowance_category.decode_to_str().lower()]

        print(max_allowance)


        # Everything below this comment is old code and unlikely to be included here


        # tax_band = person("tax_band", period)
        # tax_bands = tax_band.possible_values
        # amounts = parameters(
        #     period
        # ).gov.hmrc.income_tax.allowances.personal_savings_allowance

        # is_lowest_bands = (
        #     (tax_band == tax_bands.STARTER)
        #     | (tax_band == tax_bands.BASIC)
        #     | (tax_band == tax_bands.INTERMEDIATE)
        # )

        # return select(
        #     [
        #         tax_band == tax_bands.ADDITIONAL,
        #         tax_band == tax_bands.HIGHER,
        #         is_lowest_bands,
        #         tax_band == tax_bands.NONE,
        #     ],
        #     [amounts.additional, amounts.higher, amounts.basic, amounts.basic],
        # )

        return 0