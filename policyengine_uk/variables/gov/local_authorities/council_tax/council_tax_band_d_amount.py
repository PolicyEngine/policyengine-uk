from policyengine_uk.model_api import *


class council_tax_band_d_amount(Variable):
    value_type = float
    entity = Household
    label = "Band D council tax amount"
    documentation = (
        "The Band D council tax amount set by the household's local authority, "
        "before discounts, exemptions or Council Tax Reduction. Only one "
        "year of data is loaded (2026-27 for England and Wales, 2025-26 for "
        "Scotland), so earlier years are held flat backwards."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(household, period, parameters):
        la = household("local_authority", period).decode_to_str()
        amounts = parameters(period).gov.local_authorities.council_tax.band_d.amounts
        # Dict lookup rather than bracket indexing: Northern Ireland (domestic
        # rates, not council tax) and six post-2021 unitary authorities absent
        # from the LocalAuthority enum have no Band D amount, and should return
        # zero rather than raise.
        return np.array([amounts._children.get(a, 0) for a in la], dtype=float)
