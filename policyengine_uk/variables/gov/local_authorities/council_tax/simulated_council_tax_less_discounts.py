from policyengine_uk.model_api import *


class simulated_council_tax_less_discounts(Variable):
    value_type = float
    entity = Household
    label = "Simulated council tax after statutory discounts"
    documentation = (
        "Simulated gross council tax less the statutory discount, on a "
        "consistent basis across Great Britain so that a UK aggregate does not "
        "mix a net-of-discount England with a gross Wales and Scotland. The "
        "discount is that of section 11 of the Local Government Finance Act "
        "1992 in England, section 79 in Scotland, and section 11 until 31 "
        "March 2026 and then the regulations under section 11E in Wales; see "
        "council_tax_discount_rate for the citations and for how the "
        "no-resident case differs between the three. Northern Ireland levies "
        "domestic rates rather than council tax and is zero throughout.\n\n"
        "This figure is before exemptions, the section 11A and Welsh "
        "equivalent billing-authority determinations, the section 11B and 11C "
        "long-term-empty and second-home premiums and their Welsh "
        "counterparts in sections 12A and 12B, and Council Tax Reduction.\n\n"
        "Disregarded-person categories are not yet modelled, so the discount "
        "is understated for households containing disregarded adults; see "
        "council_tax_discount_rate."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(household, period, parameters):
        gross = household("simulated_council_tax", period)
        discount_rate = household("council_tax_discount_rate", period)
        return gross * (1 - discount_rate)
