from policyengine_uk.model_api import *


class ni_class_4_loss_relief(Variable):
    value_type = float
    entity = Person
    label = "Trading losses deducted from Class 4 profits"
    documentation = (
        "Trading losses set against the year's Class 4 profits under SSCBA "
        "1992 Sch. 2 para. 3: the current year's trading_loss and losses "
        "brought forward, up to the profits. Unlike income tax, a loss only "
        "ever reduces trade profits for Class 4: where it is set against "
        "other income for income tax, it still reduces the year's Class 4 "
        "profits, and any excess is carried forward (para. 3(4))."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Social Security Contributions and Benefits Act 1992, Sch. 2 para. 3",
        href="https://www.legislation.gov.uk/ukpga/1992/4/schedule/2/paragraph/3",
    )

    def formula(person, period, parameters):
        losses = max_(person("trading_loss", period), 0) + max_(
            person("ni_class_4_losses_brought_forward", period), 0
        )
        profits = person("ni_class_4_profits_before_losses", period)
        return min_(losses, profits)
