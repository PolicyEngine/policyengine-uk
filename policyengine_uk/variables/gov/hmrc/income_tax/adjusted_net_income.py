from policyengine_uk.model_api import *


class adjusted_net_income(Variable):
    value_type = float
    entity = Person
    label = "Adjusted net income"
    documentation = (
        "Income after the gross Gift Aid and relieved pension contribution "
        "adjustments in ITA 2007 s.58. The model's net_income is before "
        "pension relief, so both relieved employee and personal contributions "
        "are deducted here. Pension relief separately enters allowances once "
        "when calculating the income charged to tax."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 58",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/58",
    )
    unit = GBP

    def formula(person, period, parameters):
        # s.58 deducts gross Gift Aid and relieved RAS. The model also holds
        # employee contributions gross in net_income, with their relief in
        # allowances, so deduct that relief here too. Taxable-income bases
        # continue to use net_income and allowances: no second deduction.
        return (
            person("net_income", period)
            - person("gift_aid_grossed_up", period)
            - person("pension_contributions_relief", period)
        )
