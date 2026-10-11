from policyengine_uk.model_api import *


class non_savings_taxable_income(Variable):
    value_type = float
    entity = Person
    label = "Taxable income other than savings and dividend income"
    documentation = (
        "The part of taxable income below savings and dividend income, which "
        "ITA 2007 s. 16 treats as the highest part of total income: "
        "earned_taxable_income plus property income after allowances. "
        "earned_taxable_income leaves property income out because "
        "property_income_tax taxes it separately, but property income still "
        "fills the bands before savings and dividends do."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 16",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/16",
    )
    unit = GBP

    def formula(person, period, parameters):
        return person("earned_taxable_income", period) + person(
            "taxable_property_income_after_allowances", period
        )
