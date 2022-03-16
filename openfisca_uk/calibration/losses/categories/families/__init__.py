from openfisca_uk.calibration.losses.categories.families.by_program_participation import (
    FamiliesByProgramParticipation,
)
from openfisca_uk.calibration.losses.categories.families.in_total import (
    FamiliesInTotal,
)
from openfisca_uk.calibration.losses.loss_category import (
    combine_loss_categories,
)

Families = combine_loss_categories(
    FamiliesByProgramParticipation, FamiliesInTotal, label="Families"
)
