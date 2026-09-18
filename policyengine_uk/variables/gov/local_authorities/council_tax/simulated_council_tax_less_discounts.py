from policyengine_uk.model_api import *


class simulated_council_tax_less_discounts(Variable):
    value_type = float
    entity = Household
    label = "Simulated council tax after statutory discounts"
    documentation = (
        "Simulated gross council tax less the statutory discount under section "
        "11 of the Local Government Finance Act 1992 (England). Before "
        "exemptions, section 11A determinations, the section 11B and 11C "
        "long-term-empty and second-home premiums, and Council Tax Reduction.\n\n"
        "Schedule 1 disregarded-person categories are not yet modelled, so the "
        "discount is understated for households containing disregarded adults; "
        "see council_tax_discount_rate."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(household, period, parameters):
        gross = household("simulated_council_tax", period)
        discount_rate = household("council_tax_discount_rate", period)
        return gross * (1 - discount_rate)
