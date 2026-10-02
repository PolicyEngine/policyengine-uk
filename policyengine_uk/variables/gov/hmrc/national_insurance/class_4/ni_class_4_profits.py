from policyengine_uk.model_api import *


class ni_class_4_profits(Variable):
    value_type = float
    entity = Person
    label = "Profits for Class 4 NICs"
    documentation = (
        "Self-employment profits after the trade loss deductions Schedule 2 "
        "para 3 SSCBA 1992 carries over from Income Tax: losses brought forward "
        "(ITA 2007 s.83) and the year's trade loss relief against general "
        "income (s.64), which para 3(4)(a) treats as reducing the profits of "
        "any of the person's trades for Class 4, whatever income it was set "
        "against for Income Tax. A loss never reduces other income for Class 4 "
        "and the result is never negative. Capital allowances and the trading "
        "allowance are not deducted here, as before."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 15",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/15",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 Sch. 2 para. 3",
            href="https://www.legislation.gov.uk/ukpga/1992/4/schedule/2/paragraph/3",
        ),
    ]

    def formula(person, period, parameters):
        return max_(
            0,
            person("self_employment_income", period)
            - person("loss_relief", period)
            - person("trade_loss_relief_against_general_income", period),
        )
