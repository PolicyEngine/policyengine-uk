from openfisca_uk.calibration.losses.categories.populations.by_age_band import (
    PopulationsByAgeBand,
)
from openfisca_uk.calibration.losses.loss_category import (
    combine_loss_categories,
)

Populations = combine_loss_categories(
    PopulationsByAgeBand,
)
