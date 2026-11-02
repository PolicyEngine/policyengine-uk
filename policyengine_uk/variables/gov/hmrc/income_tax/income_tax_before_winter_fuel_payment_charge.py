from policyengine_uk.model_api import *


class income_tax_before_winter_fuel_payment_charge(Variable):
    value_type = float
    entity = Person
    label = "Income Tax before the winter fuel payment charge"
    documentation = (
        "Income Tax liability before the winter fuel payment charge is added "
        "at Step 7. This is the Step 5 tax less the capped Step 6 reductions, "
        "plus the other Step 7 charges. The means tests deduct this rather "
        "than income_tax: the "
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
        # ITA 2007 s. 29(2) limits reductions to the Step 5 tax. Add the
        # non-WFP Step 7 charges only after that deduction, so excess
        # reductions cannot offset them.
        tax_left_after_step_6 = max_(
            0,
            person("income_tax_pre_charges", period)
            - person("income_tax_reductions", period),
        )
        return tax_left_after_step_6 + person("income_tax_charges", period)
