from typing import List, Tuple
import numpy as np
from openfisca_core.parameters import Parameter
from openfisca_core.periods import instant
from path import Path
from tqdm import tqdm
from openfisca_uk.system import CountryTaxBenefitSystem
from openfisca_uk.tools.simulation import Microsimulation
import logging
import yaml

logging.basicConfig(level=logging.WARN)


class Program:
    """A government program with recipients who must choose to apply."""

    def __init__(
        self,
        variable: str,
        parameter: Parameter,
    ):
        self.variable = variable
        self.caseload = parameter.statistics.caseload
        self.caseload_name = self.caseload.name
        self.expenditure = parameter.statistics.expenditure
        self.expenditure_name = self.expenditure.name
        self.takeup = parameter.takeup
        self.takeup_name = self.takeup.name
        self._reset_simulation(year=2018)

    def _get_param(self, name: str):
        param = self.microsimulation.simulation.tax_benefit_system.parameters
        for part in name.split("."):
            param = getattr(param, part)
        return param

    def _reset_simulation(self, year: int = 2018):
        self.microsimulation = Microsimulation(
            year=2018 if year == 2018 else 2019
        )
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
            return np.inf, {}
        self.takeup.update(period=f"year:{year}-01-01:1", value=takeup_rate)
        values = self.microsimulation.calc(self.variable, year)
        caseload = (values > 0).sum()
        expenditure = values.sum()
        actual_caseload = self.caseload(instant(year))
        actual_expenditure = self.expenditure(instant(year))
        caseload_rel_error = abs(caseload / actual_caseload - 1)
        expenditure_rel_error = abs(expenditure / actual_expenditure - 1)
        logging.info(
            f"{self.variable_label} in {year} | {takeup_rate:.1%} -> caseload error: {caseload_rel_error:.1%}, expenditure error: {expenditure_rel_error:.1%}"
        )
        self._reset_simulation(year)
        info = dict(
            takeup_rate=takeup_rate,
            caseload=caseload,
            expenditure=expenditure,
            actual_caseload=actual_caseload,
            actual_expenditure=actual_expenditure,
            caseload_rel_error=caseload_rel_error,
            expenditure_rel_error=expenditure_rel_error,
        )
        error = (
            caseload_rel_error * (1 - self.expenditure_weight)
            + expenditure_rel_error * self.expenditure_weight
        )
        return error, info

    def fit_takeup_rate(
        self, start_year: int = 2018, end_year: int = 2022, 
        expenditure_weight: float = 0.5,
    ) -> Parameter:
        self.expenditure_weight = expenditure_weight
        takeup_parameter = self.takeup.clone()
        log = {}
        for year in tqdm(
            range(start_year, end_year + 1),
            desc=f"Solving yearly take-up rates for {self.variable_label}",
            position=1,
        ):
            takeup = 0.0
            last_error = None
            increasing = True
            step = 1
            while step > 1e-3:
                if last_error is None:
                    last_error, info = self.takeup_rate_error(takeup, year)
                    takeup += step if increasing else -step
                else:
                    error, info = self.takeup_rate_error(takeup, year)
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
            log[year] = info
            self._reset_simulation(year + 1)
        self._fitted_takeup = takeup_parameter
        return takeup_parameter, log
    

    def save_takeup(self):
        filename = Path(__file__).parent.parent / "parameters"
        parameter = self._fitted_takeup
        for part in parameter.name.split("."):
            filename = filename / part
        filename = filename.with_suffix(".yaml")
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

cb = Program(
    "child_benefit",
    parameters.hmrc.child_benefit,
)

uc = Program(
    "universal_credit",
    parameters.benefit.universal_credit,
)

ctc = Program(
    "child_tax_credit",
    parameters.benefit.tax_credits.child_tax_credit,
)

wtc = Program(
    "working_tax_credit",
    parameters.benefit.tax_credits.working_tax_credit,
)

hb = Program(
    "housing_benefit",
    parameters.benefit.housing_benefit,
)

i_s = Program(
    "income_support",
    parameters.benefit.income_support,
)

ib_jsa = Program(
    "JSA_income",
    parameters.benefit.JSA.income
)

pc = Program(
    "pension_credit",
    parameters.benefit.pension_credit
)

info = {}

programs: List[Program] = [cb, uc, ctc, wtc, hb, i_s, ib_jsa, pc]

for program in tqdm(programs, desc="Fitting take-up rates"):
    program: Program
    takeup, log = program.fit_takeup_rate(start_year=2018, end_year=2022, expenditure_weight=0.7)
    info[program.variable_label] = log
    program.save_takeup()
