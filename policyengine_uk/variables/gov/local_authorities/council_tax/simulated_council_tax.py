from policyengine_uk.model_api import *


class simulated_council_tax(Variable):
    value_type = float
    entity = Household
    label = "Simulated gross council tax"
    documentation = (
        "Gross annual council tax liability computed as the local authority's "
        "Band D amount multiplied by the statutory band ratio. Before "
        "discounts, exemptions, premiums and Council Tax Reduction."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(household, period, parameters):
        band_d = household("council_tax_band_d_amount", period)
        band = household("council_tax_band", period).decode_to_str()
        country = household("country", period).decode_to_str()
        ratios = parameters(period).gov.local_authorities.council_tax.band_ratios

        ratio = np.ones_like(band_d, dtype=float)
        for key, node in (
            ("ENGLAND", ratios.england),
            ("WALES", ratios.wales),
            ("SCOTLAND", ratios.scotland),
        ):
            table = node._children
            values = np.array([float(table.get(b, 1)) for b in band], dtype=float)
            ratio = np.where(country == key, values, ratio)

        # Northern Ireland uses domestic rates, not council tax.
        return np.where(country == "NORTHERN_IRELAND", 0, band_d * ratio)
