from typing import Union
import yaml
from pathlib import Path
from openfisca_uk import Microsimulation
from openfisca_uk_data import FRSEnhanced
import pytest

with open(Path(__file__).parent / "statistics.yaml") as f:
    statistics = yaml.load(f, Loader=yaml.SafeLoader)

sim_2018 = Microsimulation(dataset=FRSEnhanced, year=2018)
sim_2019 = Microsimulation(dataset=FRSEnhanced, year=2019)
variables = sim_2018.simulation.tax_benefit_system.variables

def get_openfisca_uk_aggregate(variable: str, year: int) -> float:
    if year == 2018:
        sim = sim_2018
    else:
        sim = sim_2019
    return sim.calc(variable, period=year).sum()

class CloserThanUKMOD:
    def __init__(self, variable: str, statistic: str, year: int):
        self.variable = variable
        self.statistic = statistic
        self.year = year

    def __call__(self):
        openfisca_uk_aggregate = get_openfisca_uk_aggregate(self.variable, self.year)
        ukmod_aggregate = statistics[self.variable]["ukmod"][self.statistic][self.year]
        official_aggregate = statistics[self.variable]["official"][self.statistic][self.year]
        openfisca_uk_error = abs(openfisca_uk_aggregate - official_aggregate)
        ukmod_error = abs(ukmod_aggregate - official_aggregate)
        return openfisca_uk_error < ukmod_error

    def __repr__(self):
        variable_name = variables[self.variable].label
        return f"OpenFisca-UK {variable_name} {self.statistic} is closer to official aggregate than UKMOD in {self.year}"

tests = []

for variable in statistics:
    variable_tests = statistics[variable]["test"]
    if "closer_than_ukmod" in variable_tests:
        for statistic in ("aggregate", "caseload"):
            if statistic in statistics[variable]["ukmod"]:
                for year in statistics[variable]["ukmod"][statistic]:
                    tests += [CloserThanUKMOD(variable, statistic, year)]

@pytest.mark.parametrize("test", tests, ids=str)
def test_statistics(test):
    assert test()
