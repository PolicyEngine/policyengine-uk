from policyengine_uk.model_api import *


class ni_class_4_losses_brought_forward(Variable):
    value_type = float
    entity = Person
    label = "Class 4 losses brought forward"
    documentation = (
        "Trade losses of earlier years that reduce this year's Class 4 profits "
        "but not Income Tax: the excess that SSCBA 1992 Sch 2 para 3(4)(b) "
        "carries forward where Income Tax set an earlier year's loss against "
        "income other than the trade's profits. Losses brought forward for "
        "both Income Tax and Class 4 go in loss_relief instead."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    reference = dict(
        title="Social Security Contributions and Benefits Act 1992 Sch. 2 para. 3(4)(b)",
        href="https://www.legislation.gov.uk/ukpga/1992/4/schedule/2/paragraph/3",
    )
