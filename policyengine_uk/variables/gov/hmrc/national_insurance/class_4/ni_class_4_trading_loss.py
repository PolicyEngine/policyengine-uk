from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import supplied_input


class ni_class_4_trading_loss(Variable):
    value_type = float
    entity = Person
    label = "Trading losses made in the year, for Class 4"
    documentation = (
        "The year's trading_loss where one is supplied for the year and "
        "ordinary expense treatment is chosen, and nil otherwise. The "
        "trading allowance recomputes every relevant trade's profits and "
        "losses for Income Tax and Class 4, so current losses cannot also "
        "be claimed. Earlier unrelieved Class 4 balances remain separate. "
        "Like other inputs, trading_loss carries an earlier "
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
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783AF",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AF",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783AI",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AI",
        ),
        dict(
            title="HMRC Business Income Manual BIM86052",
            href="https://www.gov.uk/hmrc-internal-manuals/business-income-manual/bim86052",
        ),
        dict(
            title="HMRC National Insurance Manual NIM24610",
            href="https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim24610",
        ),
    ]

    def formula(person, period, parameters):
        # Only a supplied value is a loss made in the year. Reading
        # trading_loss through the engine would return an earlier year's loss
        # carried into this one, and relieve it again.
        loss = supplied_input(person, "trading_loss", period)
        if loss is None:
            return person.empty_array()
        # Class 4 uses the same year's recomputed trade profit or loss as
        # Income Tax. A positive allowance deduction means the taxpayer
        # chose allowance treatment and gave up ordinary current losses.
        # This leaves independently carried earlier Class 4 losses intact.
        allowance_chosen = person("trading_allowance_deduction", period) > 0
        return where(allowance_chosen, 0, max_(loss, 0))
