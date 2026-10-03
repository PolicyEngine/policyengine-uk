from policyengine_uk.model_api import *


class marriage_allowance_transferable_amount(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance transferable amount"
    documentation = (
        "The fixed amount of personal allowance a Marriage Allowance election "
        "transfers: 10% of the personal allowance in ITA 2007 s. 35(1), "
        "rounded up to a multiple of £10. It does not depend on how much of "
        "the transferor's allowance is unused."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 55B(4) and (5)",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
    )
    unit = GBP

    def formula(person, period, parameters):
        allowances = parameters(period).gov.hmrc.income_tax.allowances
        ma = allowances.marriage_allowance
        amount = allowances.personal_allowance.amount * ma.max
        increment = ma.rounding_increment
        return np.ceil(amount / increment) * increment
