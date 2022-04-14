from openfisca_uk.data.datasets.frs.enhanced.stages.calibration.losses.categories.populations.by_age_band import (
    PopulationsByAgeBand,
)
from .by_age_sex_region import PopulationsByAgeSexRegion
from .by_income_tax_band import (
    PopulationsByIncomeTaxBand,
)
from .by_region import (
    PopulationsByRegion,
)
from .in_total import (
    PopulationsInTotal,
)
from openfisca_uk.data.datasets.frs.enhanced.stages.calibration.losses.loss_category import (
    combine_loss_categories,
)


Populations = combine_loss_categories(
    PopulationsByAgeBand,
    PopulationsByIncomeTaxBand,
    PopulationsInTotal,
    label="Populations",
)
