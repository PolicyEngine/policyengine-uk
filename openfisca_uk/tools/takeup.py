from typing import Tuple
import numpy as np
from openfisca_core.parameters import Parameter
from openfisca_core.periods import instant
from path import Path
from tqdm import tqdm
from openfisca_uk.system import CountryTaxBenefitSystem
from openfisca_uk.tools.simulation import Microsimulation
import logging
import yaml

logging.basicConfig(level=logging.INFO)


class Program:
    """A government program with receipients who must choose to apply."""

    def __init__(
        self,
        variable: str,
        caseload: Parameter,
        expenditure: Parameter,
        takeup: Parameter,
        expenditure_weight: float = 0.5,
    ):
        self.variable = variable
        self.caseload = caseload
        self.caseload_name = caseload.name
        self.expenditure = expenditure
        self.expenditure_name = expenditure.name
        self.takeup = takeup
        self.takeup_name = takeup.name
        self.expenditure_weight = expenditure_weight
        self._reset_simulation()

    def _get_param(self, name: str):
        param = self.microsimulation.simulation.tax_benefit_system.parameters
        for part in name.split("."):
            param = getattr(param, part)
        return param

    def _reset_simulation(self):
        self.microsimulation = Microsimulation()
        self.variable_label = (
            self.microsimulation.simulation.tax_benefit_system.variables[
                self.variable
            ].label
        )
        self.takeup = self._get_param(self.takeup_name)
        self.caseload = self._get_param(self.caseload_name)
        self.expenditure = self._get_param(self.expenditure_name)

    def takeup_rate_error(self, takeup_rate: float, year: int) -> float:
        if takeup_rate < 0 or takeup_rate > 1:
            return np.inf
        self.takeup.update(period=f"year:{year}-01-01:1", value=takeup_rate)
        values = self.microsimulation.calc(self.variable, year)
        caseload = (values > 0).sum()
        expenditure = values.sum()
        actual_caseload = self.caseload(instant(year))
        actual_expenditure = self.expenditure(instant(year))
        caseload_rel_error = abs(caseload / actual_caseload - 1)
        expenditure_rel_error = abs(expenditure / actual_expenditure - 1)
        self._reset_simulation()
        return (
            caseload_rel_error * self.expenditure_weight
            + expenditure_rel_error * (1 - self.expenditure_weight)
        )

    def fit_takeup_rate(
        self, start_year: int = 2019, end_year: int = 2022
    ) -> Parameter:
        takeup_parameter = self.takeup.clone()
        for year in tqdm(
            range(start_year, end_year + 1),
            desc=f"Solving yearly take-up rates for {self.variable_label}",
        ):
            takeup = 0.0
            last_error = None
            increasing = True
            step = 1
            while step > 1e-3:
                if last_error is None:
                    last_error = self.takeup_rate_error(takeup, year)
                    takeup += step if increasing else -step
                else:
                    error = self.takeup_rate_error(takeup, year)
                    change = error - last_error
                    last_error = error
                    step /= 2
                    if change > 0:
                        increasing = not increasing
                        step *= 2
                    takeup += step if increasing else -step
            takeup_parameter.update(
                period=f"year:{year}-01-01:1", value=round(takeup, 3)
            )
        return takeup_parameter


def save_parameter(parameter: Parameter, filename: Path):
    with open(filename, "w") as f:
        param = yaml.dump(
            {
                "description": parameter.description,
                "metadata": parameter.metadata,
            }
        )
        param += "values:"
        for param_instant in parameter.values_list:
            param += f"\n  {param_instant.instant_str}: {param_instant.value}"
        param += "\n"
        f.write(param)
    logging.info(f"Saved parameter {parameter.name} to {filename}")


parameters = CountryTaxBenefitSystem().parameters

parameter_folder = Path(__file__).parent.parent / "parameters"

child_benefit = Program(
    "child_benefit",
    parameters.hmrc.child_benefit.statistics.caseload,
    parameters.hmrc.child_benefit.statistics.expenditure,
    parameters.hmrc.child_benefit.takeup_rate,
)

save_parameter(
    child_benefit.fit_takeup_rate(),
    parameter_folder / "hmrc" / "child_benefit" / "takeup_rate.yaml",
)

ctc = Program(
    "child_tax_credit",
    parameters.benefit.tax_credits.child_tax_credit.statistics.caseload,
    parameters.benefit.tax_credits.child_tax_credit.statistics.expenditure,
    parameters.benefit.tax_credits.child_tax_credit.takeup,
)

save_parameter(
    ctc.fit_takeup_rate(),
    parameter_folder
    / "benefit"
    / "tax_credits"
    / "child_tax_credit"
    / "takeup.yaml",
)

wtc = Program(
    "working_tax_credit",
    parameters.benefit.tax_credits.working_tax_credit.statistics.caseload,
    parameters.benefit.tax_credits.working_tax_credit.statistics.expenditure,
    parameters.benefit.tax_credits.working_tax_credit.takeup,
)

save_parameter(
    wtc.fit_takeup_rate(),
    parameter_folder
    / "benefit"
    / "tax_credits"
    / "working_tax_credit"
    / "takeup.yaml",
)
