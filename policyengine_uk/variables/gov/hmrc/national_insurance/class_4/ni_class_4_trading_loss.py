from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import supplied_input


class ni_class_4_trading_loss(Variable):
    value_type = float
    entity = Person
    label = "Trading losses made in the year, for Class 4"
    documentation = (
        "The year's trading_loss where one is supplied for the year, and nil "
        "otherwise. Like other inputs, trading_loss carries an earlier "
        "year's value into later years that are not set, but for Class 4 a "
        "loss is relieved once: it reduces the profits of the year it is "
        "made, and only the excess reduces the profits of later years "
        "(ni_class_4_losses_brought_forward). A loss supplied for one year "
        "is therefore not a new loss in the years after it."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992, Sch. 2 para. 3(4)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/schedule/2/paragraph/3",
        ),
        dict(
            title="Income Tax Act 2007, s. 83(2)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/83",
        ),
    ]

    def formula(person, period, parameters):
        # Only a supplied value is a loss made in the year. Reading
        # trading_loss through the engine would return an earlier year's loss
        # carried into this one, and relieve it again.
        loss = supplied_input(person, "trading_loss", period)
        if loss is None:
            return person.empty_array()
        return max_(loss, 0)
