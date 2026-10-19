import numpy as np

from policyengine_uk.model_api import *


class high_value_council_tax_surcharge(Variable):
    value_type = float
    entity = Household
    label = "High Value Council Tax Surcharge"
    documentation = (
        "Additional annual surcharge on owners of residential property in England "
        "worth at least £2 million in 2026 prices. Owners, not occupiers, are "
        "liable, so the household is charged on its main residence only where it "
        "owns that home (owned outright or with a mortgage). Let property and "
        "second homes are not modelled. The annual OBR house-price index "
        "provides a proxy for converting simulated values to the 2026 "
        "valuation basis."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.gov.uk/government/publications/high-value-council-tax-surcharge/high-value-council-tax-surcharge",
        "https://www.gov.uk/government/consultations/high-value-council-tax-surcharge/high-value-council-tax-surcharge",
    ]

    def formula(household, period, parameters):
        if period.start.year < 2028:
            return 0

        country = household("country", period)
        in_england = country == country.possible_values.ENGLAND

        # Owners, rather than occupiers, are liable (Budget 2025 HVCTS policy
        # paper; MHCLG consultation, "Scope of the surcharge").
        tenure = household("tenure_type", period)
        tenures = tenure.possible_values
        owns_home = (tenure == tenures.OWNED_OUTRIGHT) | (
            tenure == tenures.OWNED_WITH_MORTGAGE
        )

        p = parameters(period)
        property_value = household("main_residence_value", period)
        current_index = p.gov.economic_assumptions.indices.obr.house_prices
        baseline_index = parameters(
            "2026"
        ).gov.economic_assumptions.indices.obr.house_prices
        charge_scale = p.gov.hmrc.council_tax.high_value_surcharge.amount.copy()
        # Compare prices and fixed 2026 bands in the same stored precision;
        # inverse division can put a projected exact boundary in a lower band.
        charge_scale.thresholds = (
            np.array(charge_scale.thresholds, dtype=property_value.dtype)
            * (current_index / baseline_index)
        ).tolist()
        surcharge = charge_scale.calc(property_value)
        return where(in_england & owns_home, surcharge, 0)
