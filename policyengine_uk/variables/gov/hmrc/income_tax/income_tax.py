from policyengine_uk.model_api import *


class income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax"
    documentation = (
        "Total Income Tax liability: the liability before the winter fuel "
        "payment charge, plus the charge, which is additional tax added at "
        "Step 7 after tax reductions."
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
    )
    category = TAX
    adds = [
        "income_tax_before_winter_fuel_payment_charge",
        "winter_fuel_payment_charge",
    ]
