from policyengine_uk.model_api import *


class income_tax_reductions(Variable):
    value_type = float
    entity = Person
    label = "Income Tax reductions"
    documentation = (
        "The tax reductions deducted at Step 6 of the Income Tax calculation. "
        "A reduction may be deducted only so far as there is tax calculated at "
        "Step 5 to deduct it from, counting the reductions already deducted. "
        "So the total is the reductions on the Step 6 list, each limited by "
        "its own rules, up to the Step 5 tax, whatever the order of deduction. "
        "The reductions never reduce the charges added at Step 7, such as the "
        "High Income Child Benefit Charge. Section 29(4A) also limits the EIS, "
        "SEIS, social investment, VCT and community investment reductions to "
        "the Step 5 tax less the tax treated as deducted from Gift Aid "
        "donations. That limit is not applied, as other_tax_credits holds "
        "those reductions together with maintenance and foreign tax relief."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax Act 2007 s. 23 (Step 6)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        ),
        dict(
            title="Income Tax Act 2007 s. 29",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
    ]

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        reductions = max_(0, add(person, period, income_tax.step_6_tax_reductions))
        step_5_tax = max_(0, person("income_tax_pre_charges", period))
        return min_(reductions, step_5_tax)
