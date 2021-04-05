from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

"""
This file calculates the overall liability for Income Tax.
"""

class earned_taxable_income(Variable):
    value_type = float
    entity = Person
    label = u'Non-savings, non-dividend income for Income Tax'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 10"

    def formula(person, period, parameters):
        COMPONENTS = [
            "taxable_employment_income",
            "taxable_pension_income",
            "taxable_social_security_income",
            "taxable_trading_income",
            "taxable_property_income",
            "taxable_miscellaneous_income"
        ]
        ALLOWANCES = [
            "personal_allowance",
            "blind_persons_allowance",
            "marriage_allowance",
            "trading_allowance",
            "property_allowance"
        ]
        amount = add(person, period, COMPONENTS)
        reductions = add(person, period, ALLOWANCES)
        final_amount = max_(0, amount - reductions)
        return final_amount

class earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Income tax on earned income'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 10"

    def formula(person, period, parameters):
        rates = parameters(period).taxes.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        scot_amount = rates.scotland.calc(person("earned_taxable_income", period))
        amount = where(scot, scot_amount, uk_amount)
        return amount

class TaxBand(Enum):
    NONE = "None"
    BASIC = "Basic"
    HIGHER = "Higher"
    ADDITIONAL = "Additional"

class pays_scottish_income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Whether the individual pays Scottish Income Tax rates'
    definition_period = YEAR

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        return person.household("country", period) == countries.SCOTLAND

class tax_band(Variable):
    value_type = Enum
    possible_values = TaxBand
    default_value = TaxBand.NONE
    entity = Person
    label = u"Tax band of the individual"
    definition_period = YEAR

    def formula(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).taxes.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        basic = allowances + where(scot, rates.scotland.thresholds[0], rates.uk.thresholds[0])
        higher = allowances + where(scot, rates.scotland.thresholds[-2], rates.uk.thresholds[-2])
        add = allowances + where(scot, rates.scotland.thresholds[-1], rates.uk.thresholds[-1])
        band = select([ANI >= add, ANI >= higher, ANI > basic, ANI <= basic], [TaxBand.ADDITIONAL, TaxBand.HIGHER, TaxBand.BASIC, TaxBand.NONE])
        return band