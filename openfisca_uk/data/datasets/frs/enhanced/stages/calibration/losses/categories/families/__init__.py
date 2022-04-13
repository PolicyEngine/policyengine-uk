from .by_program_participation import (
    FamiliesByProgramParticipation,
)
from .in_total import (
    FamiliesInTotal,
)
from openfisca_uk.data.datasets.frs.enhanced.stages.calibration.losses.loss_category import (
    combine_loss_categories,
)


Families = combine_loss_categories(
    FamiliesByProgramParticipation, FamiliesInTotal, label="Families"
)
