from policyengine_uk.model_api import *


class taxable_miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of miscellaneous income that is taxable"
    documentation = (
        "Miscellaneous income charged to income tax. A miscellaneous loss can "
        "be relieved only against miscellaneous income (ITA 2007 s. 152(4)), "
        "never against other income, so a net loss counts as nil here. Carrying "
        "the loss forward against later years' miscellaneous income is not "
        "modelled."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 574",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/574",
        ),
        dict(
            title="Income Tax Act 2007 s. 152",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/152",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        return max_(0, person("miscellaneous_income", period))
