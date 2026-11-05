from policyengine_uk.model_api import *
from policyengine_uk.utils.child_benefit import (
    child_benefit_charge_percentage,
    round_down_to_pounds,
)


class CB_HITC(Variable):
    value_type = float
    entity = Person
    label = "Child Benefit High-Income Tax Charge"
    documentation = (
        "The appropriate percentage of the Child Benefit received, charged on "
        "the partner with the higher adjusted net income. Section 681C(3) "
        "rounds down the Child Benefit total and the charge to whole pounds, "
        "and the percentage to a whole number."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 681C",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/681C",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 Part 10 Chapter 8",
            href="https://www.legislation.gov.uk/ukpga/2003/1/part/10/chapter/8",
        ),
    ]
    unit = GBP
    defined_for = "is_higher_earner"

    def formula(person, period, parameters):
        CB_received = round_down_to_pounds(person.benunit("child_benefit", period))
        hitc = parameters(period).gov.hmrc.income_tax.charges.CB_HITC
        income = person("adjusted_net_income", period)
        percentage = child_benefit_charge_percentage(
            income, hitc.phase_out_start, hitc.phase_out_end
        )
        return round_down_to_pounds(percentage * CB_received)
