from openfisca_uk.calibration.losses.categories.populations.by_age_band import (
    PopulationsByAgeBand,
)
from openfisca_uk.calibration.losses.categories.populations.by_income_tax_band import (
    PopulationsByIncomeTaxBand,
)
from openfisca_uk.calibration.losses.categories.populations.by_region import (
    PopulationsByRegion,
)
from openfisca_uk.calibration.losses.categories.populations.in_total import (
    PopulationsInTotal,
)
from openfisca_uk.calibration.losses.loss_category import (
    combine_loss_categories,
)

Populations = combine_loss_categories(
    PopulationsByAgeBand,
    PopulationsByIncomeTaxBand,
    PopulationsByRegion,
    PopulationsInTotal,
    label="Populations",
)
