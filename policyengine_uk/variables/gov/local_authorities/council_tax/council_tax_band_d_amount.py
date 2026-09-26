from policyengine_uk.model_api import *


class council_tax_band_d_amount(Variable):
    value_type = float
    entity = Household
    label = "Band D council tax amount"
    documentation = (
        "The Band D council tax amount set by the household's local authority, "
        "before discounts, exemptions or Council Tax Reduction. For England "
        "and Wales this is the area figure, which includes the county, police, "
        "fire, combined authority and parish or community council precepts as "
        "well as the billing authority's own charge; for Scotland it excludes "
        "the separately billed water and waste water charges. Fiscal 2025 and "
        "2026 are loaded for all three nations, so earlier years are held flat "
        "backwards from 2025."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(household, period, parameters):
        la = household("local_authority", period).decode_to_str()
        amounts = parameters(period).gov.local_authorities.council_tax.band_d.amounts
        # Dict lookup rather than bracket indexing: the LocalAuthority enum
        # also carries Northern Ireland districts (domestic rates, not council
        # tax) and historical pre-2023 English districts, neither of which has
        # a Band D amount, so those should return zero rather than raise.
        return np.array([amounts._children.get(a, 0) for a in la], dtype=float)
