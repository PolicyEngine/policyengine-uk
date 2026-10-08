from policyengine_uk.model_api import *


class ni_class_4_loss_relief(Variable):
    value_type = float
    entity = Person
    label = "Trading losses deducted from Class 4 profits"
    documentation = (
        "Trading losses set against the year's Class 4 profits under SSCBA "
        "1992 Sch. 2 para. 3: losses brought forward and the year's own "
        "loss (ni_class_4_trading_loss), up to the profits. Unlike income "
        "tax, a loss only ever reduces trade profits for Class 4: where it "
        "is set against other income for income tax, it still reduces the "
        "year's Class 4 profits, and any excess is carried forward (para. "
        "3(4)). Assumes the year's loss is claimed in that year: carry-back "
        "claims (ITA 2007 ss. 64(2)(b), 72 and 89) are not modelled. Losses "
        "are pooled across trades, though s. 83 carries a loss forward only "
        "against the same trade."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Social Security Contributions and Benefits Act 1992, Sch. 2 para. 3",
        href="https://www.legislation.gov.uk/ukpga/1992/4/schedule/2/paragraph/3",
    )

    def formula(person, period, parameters):
        losses = person("ni_class_4_trading_loss", period) + max_(
            person("ni_class_4_losses_brought_forward", period), 0
        )
        profits = person("ni_class_4_profits_before_losses", period)
        return min_(losses, profits)
