from policyengine_uk.model_api import *


class income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax"
    documentation = (
        "Total Income Tax liability: the liability before the winter fuel "
        "payment charge, plus the charge, which is additional tax added at "
        "Step 7 after the reductions capped at the Step 5 tax. Finance Act "
        "2026 Sch. 10 para. 4(3) adds the charge to ITA 2007 s. 30(1)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        dict(
            title="Income Tax Act 2007 s. 23",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        ),
        dict(
            title="Income Tax Act 2007 s. 30",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/30",
        ),
        dict(
            title="Finance Act 2026 Sch. 10 para. 4(3)",
            href="https://www.legislation.gov.uk/ukpga/2026/11/schedule/10/paragraph/4",
        ),
    )
    # The winter fuel payment charge is a Step 7 amount, alongside the other
    # s. 30 charges, but is added separately to avoid the benefit means-test
    # cycle described on income_tax_before_winter_fuel_payment_charge.
    category = TAX
    adds = [
        "income_tax_before_winter_fuel_payment_charge",
        "winter_fuel_payment_charge",
    ]
