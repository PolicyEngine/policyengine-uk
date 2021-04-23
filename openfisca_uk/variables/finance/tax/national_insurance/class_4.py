from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class NI_class_4(Variable):
    value_type = float
    entity = Person
    label = u"Class 4 Contributions for National Insurance for the year"
    definition_period = YEAR
    reference = "Social Security and Benefits Act 1992 s. 15"

    def formula(person, period, parameters):
        class_4 = parameters(period).tax.national_insurance.class_4
        profits = person("trading_income", period)
        main_amount = amount_between(
            profits,
            class_4.thresholds.lower_profits_limit,
            class_4.thresholds.upper_profits_limit,
        )
        add_amount = amount_over(
            profits, class_4.thresholds.upper_profits_limit
        )
        charge = (
            main_amount * class_4.rates.main
            + add_amount * class_4.rates.additional
        )
        return charge


class national_insurance(Variable):
    value_type = float
    entity = Person
    label = u"Total amount of National Insurance liability for this person"
    definition_period = YEAR
    reference = "Social Security and Benefits Act 1992 s. 1(2)"

    def formula(person, period, parameters):
        CLASSES = ["employee_NI_class_1", "NI_class_2", "NI_class_4"]
        total = add(person, period, CLASSES)
        return total
