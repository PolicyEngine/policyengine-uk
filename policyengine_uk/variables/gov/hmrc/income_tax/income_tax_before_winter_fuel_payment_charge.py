from policyengine_uk.model_api import *


class income_tax_before_winter_fuel_payment_charge(Variable):
    value_type = float
    entity = Person
    label = "Income Tax before the winter fuel payment charge"
    documentation = (
        "Income Tax liability before the winter fuel payment charge is added "
        "at Step 7. The means tests deduct this rather than income_tax: the "
        "charge is not tax on the income they assess but the recovery of a "
        "winter fuel payment, and it depends on receipt of Pension Credit "
        "and Universal Credit, so deducting it would make the model circular."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax

        additions = add(person, period, p.income_tax_additions)
        subtractions = add(person, period, p.income_tax_subtractions)

        return max_(0, additions - subtractions)
