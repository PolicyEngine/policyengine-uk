from policyengine_uk.model_api import *


class ni_class_4_losses_carried_forward(Variable):
    value_type = float
    entity = Person
    label = "Trading losses carried forward for Class 4"
    documentation = (
        "Trading losses not yet deducted from Class 4 profits at the end of "
        "the year: the year's own loss (ni_class_4_trading_loss) and losses "
        "brought forward, less those deducted this year. They reduce the "
        "Class 4 profits of the following years, earliest first (SSCBA 1992 "
        "Sch. 2 para. 3(4)(b); ITA 2007 ss. 83 and 84)."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992, Sch. 2 para. 3(4)(b)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/schedule/2/paragraph/3",
        ),
        dict(
            title="Income Tax Act 2007, s. 84",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/84",
        ),
    ]

    def formula(person, period, parameters):
        losses = person("ni_class_4_trading_loss", period) + max_(
            person("ni_class_4_losses_brought_forward", period), 0
        )
        return losses - person("ni_class_4_loss_relief", period)
