from openfisca_uk.calibration.losses.categories.budgetary_impact.by_program import (
    BudgetaryImpactByProgram,
)
from openfisca_uk.calibration.losses.categories.budgetary_impact.by_income_source import (
    BudgetaryImpactByIncomeSource,
)
from openfisca_uk.calibration.losses.categories.budgetary_impact.by_program_by_country import (
    BudgetaryImpactByProgramByCountry,
)
from openfisca_uk.calibration.losses.categories.budgetary_impact.of_income_tax_by_income_band import (
    BudgetaryImpactOfIncomeTaxByIncomeBand,
)
from openfisca_uk.calibration.losses.loss_category import (
    combine_loss_categories,
)

BudgetaryImpact = combine_loss_categories(
    BudgetaryImpactByProgram,
    BudgetaryImpactByIncomeSource,
    BudgetaryImpactByProgramByCountry,
    BudgetaryImpactOfIncomeTaxByIncomeBand,
    label="Budgetary impact",
    weight=3,
)
