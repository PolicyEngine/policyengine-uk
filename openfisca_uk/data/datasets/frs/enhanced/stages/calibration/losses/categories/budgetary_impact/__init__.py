from .by_program import (
    BudgetaryImpactByProgram,
)
from .by_income_source import (
    BudgetaryImpactByIncomeSource,
)
from .by_program_by_country import (
    BudgetaryImpactByProgramByCountry,
)
from .of_income_tax_by_income_band import (
    BudgetaryImpactOfIncomeTaxByIncomeBand,
)
from openfisca_uk.data.datasets.frs.enhanced.stages.calibration.losses.loss_category import (
    combine_loss_categories,
)


BudgetaryImpact = combine_loss_categories(
    BudgetaryImpactByProgram,
    BudgetaryImpactByIncomeSource,
    BudgetaryImpactByProgramByCountry,
    BudgetaryImpactOfIncomeTaxByIncomeBand,
    label="Budgetary impact",
)
