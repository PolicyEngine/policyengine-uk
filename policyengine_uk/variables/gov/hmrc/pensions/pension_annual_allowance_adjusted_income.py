from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import annual_allowance_net_income


class pension_annual_allowance_adjusted_income(Variable):
    value_type = float
    entity = Person
    label = "Adjusted income for the pension annual allowance"
    documentation = (
        "FA 2004 s. 228ZA(4) adjusted income. Model net_income precedes pension "
        "relief, so net-pay and claimed relief are already restored. Add the "
        "total pension input amount less the individual's own contributions, "
        "and exclude taxable lump-sum death benefits already included in "
        "income. The pension input amount can be supplied to include statutory "
        "defined-benefit accrual; its default is a cash-contribution proxy. "
        "The NICs-only excess enters neither model income nor member "
        "contributions. All actual own contributions are "
        "subtracted, including unrelievable contributions from age 75."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA/4"

    def formula(person, period, parameters):
        actual_income = annual_allowance_net_income(person, period, parameters)
        actual_member_contributions = person("pension_contributions", period)
        return (
            actual_income
            + person("pension_contributions_for_annual_allowance", period)
            - actual_member_contributions
            - person("pension_annual_allowance_taxable_lump_sum_death_benefits", period)
        )
