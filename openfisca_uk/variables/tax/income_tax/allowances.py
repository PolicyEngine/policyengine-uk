from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *
from openfisca_uk.variables.tax.income_tax.liability import TaxBand

"""
This file calculates the allowances to which taxpayers are entitled. This follows step 3 of the Income Tax Act 2007 s. 23.
"""

class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Personal Allowance for the year'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        PA = parameters(period).taxes.income_tax.allowances.personal_allowance
        ANI = person("adjusted_net_income", period)
        excess = max_(0, ANI - PA.maximum_ANI)
        reduction = excess * PA.reduction_rate
        amount = max_(0, PA.amount - reduction)
        return amount

class blind_persons_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Blind Person\'s Allowance for the year (not simulated)'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 38"

class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 55"

class trading_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Trading Allowance for the year'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"

    def formula(person, period, parameters):
        return parameters(period).taxes.income_tax.allowances.trading_allowance

class trading_income_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u'Deduction applied by the trading allowance'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"

    def formula(person, period, parameters):
        amount = max_(0, person("trading_allowance", period) - person("trading_income", period))
        return amount

class property_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Property Allowance for the year'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783BF"

    def formula(person, period, parameters):
        return parameters(period).taxes.income_tax.allowances.rental_allowance

class property_income_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u'Deduction applied by the property allowance'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"

    def formula(person, period, parameters):
        amount = max_(0, person("property_allowance", period) - person("property_income", period))
        return amount


class savings_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Savings Allowance for the year'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12B"

    def formula(person, period, parameters):
        tax_band = person("tax_band", period)
        tax_bands = tax_band.possible_values
        amounts = parameters(period).taxes.income_tax.allowances.personal_savings_allowance
        allowance = select([
            tax_band == tax_bands.ADDITIONAL, 
            tax_band == tax_bands.HIGHER, 
            tax_band == tax_bands.BASIC, 
            tax_band == tax_bands.NONE], 
        [
            amounts.additional,
            amounts.higher,
            amounts.basic,
            amounts.basic
        ])
        return allowance

class allowances(Variable):
    value_type = float
    entity = Person
    label = u'Allowances applicable to adjusted net income'
    definition_period = YEAR

    def formula(person, period, parameters):
        ALLOWANCES = [
            "personal_allowance",
            "blind_persons_allowance",
            "property_income_allowance_deduction",
            "trading_income_allowance_deduction"
        ]
        allowance = add(person, period, ALLOWANCES)
        return allowance

