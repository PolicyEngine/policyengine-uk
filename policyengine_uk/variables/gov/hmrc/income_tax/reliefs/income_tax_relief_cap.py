from policyengine_uk.model_api import *


class income_tax_relief_cap(Variable):
    value_type = float
    entity = Person
    label = "Cap on certain Income Tax reliefs"
    documentation = (
        "The most that the reliefs listed in ITA 2007 s.24A(6), of which the "
        "model has trade loss relief against general income, can deduct at "
        "Step 2 in the year: '£50,000, or ... if more, 25% of the taxpayer's "
        "adjusted total income' (s.24A(5)). Deductions from profits of the "
        "loss-making trade itself fall outside the cap (s.24A(7)(b)); in the "
        "loss-making year that trade has no profits."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 24A",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/24A",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax.reliefs.cap
        return max_(p.amount, p.rate * person("adjusted_total_income", period))
