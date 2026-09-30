from policyengine_uk.model_api import *


class ni_class_4_profits(Variable):
    value_type = float
    entity = Person
    label = "Profits chargeable to Class 4 NICs"
    documentation = (
        "Trade profits chargeable to income tax under ITTOIA 2005 Part 2 "
        "Chapter 2 (after capital allowances and the trading allowance), less "
        "trading losses as SSCBA 1992 Sch. 2 para. 3 allows. Personal "
        "reliefs, interest relief and pension contributions are not deducted "
        "(para. 3(2)), and neither are Class 1 contributions."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992, s. 15(1) and (3)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/15",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992, Sch. 2 paras. 2 and 3",
            href="https://www.legislation.gov.uk/ukpga/1992/4/schedule/2",
        ),
    ]

    def formula(person, period, parameters):
        profits = person("ni_class_4_profits_before_losses", period)
        loss_relief = person("ni_class_4_loss_relief", period)
        return max_(profits - loss_relief, 0)
