from policyengine_uk.model_api import *


class property_receipts_within_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Property receipts are within the property allowance"
    documentation = (
        "Whether the person's relevant property income (gross receipts) does "
        "not exceed the property allowance, so that full relief applies unless "
        "the person elects out of it. Without gross receipts, a "
        "property_income within the allowance is taken as coming from "
        "receipts within it. property_income is measured before finance "
        "costs, so receipts are never below it."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, s. 783BE",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BE",
    )

    def formula(person, period, parameters):
        allowance = parameters(period).gov.hmrc.income_tax.allowances.property_allowance
        profit = person("property_income", period)
        receipts = person("property_rental_income", period)
        # Receipts below profit (including the default zero) mean unknown.
        receipts_known = (receipts > 0) & (receipts >= profit)
        return where(receipts_known, receipts <= allowance, profit <= allowance)
