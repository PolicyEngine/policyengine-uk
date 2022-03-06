from openfisca_uk.calibration.losses.categories.households.in_total import (
    HouseholdsInTotal,
)
from openfisca_uk.calibration.losses.categories.households.by_region_by_council_tax_band import (
    HouseholdsByRegionByCouncilTaxBand,
)
from openfisca_uk.calibration.losses.categories.households.by_region_by_tenure_type import (
    HouseholdsByRegionByTenureType,
)
from openfisca_uk.calibration.losses.loss_category import (
    combine_loss_categories,
)

Households = combine_loss_categories(
    HouseholdsInTotal,
    HouseholdsByRegionByCouncilTaxBand,
    HouseholdsByRegionByTenureType,
    label="Households",
)
