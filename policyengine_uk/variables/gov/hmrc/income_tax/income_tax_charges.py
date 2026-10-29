from policyengine_uk.model_api import *


class income_tax_charges(Variable):
    value_type = float
    entity = Person
    label = "Income Tax charges"
    documentation = (
        "The charges to Income Tax added at Step 7 of the Income Tax "
        "calculation, after the tax reductions, such as the High Income Child "
        "Benefit Charge and the pension annual allowance charge. Tax "
        "reductions do not offset them. The winter fuel payment charge is also "
        "a Step 7 charge (Finance Act 2026 Sch. 10 para. 4(3)), but income_tax "
        "adds it separately after income_tax_before_winter_fuel_payment_charge "
        "to avoid the cycle through benefit means tests."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax Act 2007 s. 23 (Step 7)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        ),
        dict(
            title="Income Tax Act 2007 s. 30(1)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/30",
        ),
    ]

    adds = "gov.hmrc.income_tax.step_7_additional_tax"
