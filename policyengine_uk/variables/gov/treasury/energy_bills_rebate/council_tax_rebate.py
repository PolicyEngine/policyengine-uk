from policyengine_uk.model_api import *


class ebr_council_tax_rebate(Variable):
    label = "Council Tax Rebate (EBR)"
    documentation = (
        "Council Tax discount under the Energy Bills Rebate. England's £150 "
        "Council Tax Rebate went to households in bands A to D (billing "
        "authority guidance, paragraphs 2 and 11), and Scotland and Wales "
        "paid their own £150 awards to the same bands. Northern Ireland "
        "levies domestic rates, not council tax, and had no Council Tax "
        "Rebate; its households received the £600 Energy Bills Support "
        "Scheme payment. The model doesn't pay the Scottish and Welsh awards "
        "to Council Tax Reduction recipients in bands E and above."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.gov.uk/government/publications/the-council-tax-rebate-2022-23-billing-authority-guidance/support-for-energy-bills-the-council-tax-rebate-2022-23-billing-authority-guidance",
        "https://www.gov.scot/publications/local-government-finance-circular-2-2022-guidance-to-local-authorities-april-2022-cost-of-living-award/",
        "https://www.gov.wales/cost-living-support-scheme-guide-local-authorities-html",
        "https://www.legislation.gov.uk/nisi/1977/2157/contents",
    )

    def formula(household, period, parameters):
        ctr = parameters(period).gov.treasury.energy_bills_rebate.council_tax_rebate
        ct_band = household("council_tax_band", period)
        ct_band_values = ct_band.possible_values
        eligible = np.any(
            np.array([ct_band == getattr(ct_band_values, band) for band in ctr.bands]),
            axis=0,
        )
        # Northern Ireland has no council tax bands, so its input band means
        # nothing here (the enhanced FRS gives every NI household band A).
        country = household("country", period)
        has_council_tax = country != country.possible_values.NORTHERN_IRELAND
        return has_council_tax * eligible * ctr.amount
