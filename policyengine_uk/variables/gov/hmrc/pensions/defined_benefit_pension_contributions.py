from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import workplace_pension_contributions


class defined_benefit_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Workplace pension contributions paid into defined-benefit arrangements"
    documentation = (
        "The defined_benefit_pension_share of the person's workplace pension "
        "contributions: employer contributions, actual employee "
        "contributions under a net pay arrangement and full salary "
        "sacrifice. These contributions are not a pension input amount: the "
        "annual allowance counts defined_benefit_pension_input_amount for "
        "them instead."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Finance Act 2004 s. 234",
        href="https://www.legislation.gov.uk/ukpga/2004/12/section/234",
    )

    def formula(person, period, parameters):
        share = clip(person("defined_benefit_pension_share", period), 0, 1)
        return share * workplace_pension_contributions(person, period)
