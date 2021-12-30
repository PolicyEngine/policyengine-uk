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


def get_openfisca_uk_caseload(variable: str, year: int) -> float:
    if year == 2018:
        sim = sim_2018
    else:
        sim = sim_2019
    return (sim.calc(variable, period=year) > 0).sum()


class StatisticTest:
    def __init__(self, variable: str, statistic: str, year: int, **kwargs):
        self.variable = variable
        self.year = year
        self.statistic = statistic
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def openfisca_uk(self):
        if self.statistic == "aggregate":
            return get_openfisca_uk_aggregate(self.variable, self.year)
        elif self.statistic == "caseload":
            return get_openfisca_uk_caseload(self.variable, self.year)
        raise ValueError(f"Unknown statistic: {self.statistic}")

    def stored_result(self, source: str):
        if self.statistic == "aggregate":
            return statistics[self.variable][source]["aggregate"][self.year]
        elif self.statistic == "caseload":
            return statistics[self.variable][source]["caseload"][self.year]
        raise ValueError(f"Unknown statistic: {self.statistic}")

    @property
    def ukmod(self):
        return self.stored_result("ukmod")

    @property
    def official(self):
        return self.stored_result("official")

    @property
    def variable_label(self):
        return variables[self.variable].label

    def test(self) -> bool:
        raise NotImplementedError("Test not specified")

    def describe(self) -> str:
        raise NotImplementedError("Description not specified")

    def __repr__(self):
        return self.describe()


class CloserThanUKMOD(StatisticTest):
    def test(self) -> bool:
        openfisca_uk_error = abs(self.openfisca_uk - self.official)
        ukmod_error = abs(self.ukmod - self.official)
        return openfisca_uk_error <= ukmod_error

    def describe(self):
        return f"OpenFisca-UK {self.variable_label} {self.statistic} at least as close to the official aggregate as UKMOD in {self.year}"


class AbsoluteErrorLessThan(StatisticTest):
    def test(self):
        openfisca_uk_error = abs(self.openfisca_uk - self.official)
        return openfisca_uk_error < self.max_error

    def describe(self):
        return f"OpenFisca-UK {self.variable_label} {self.statistic} absolute error is less than {self.max_error:,} in {self.year}"


class RelativeErrorLessThan(StatisticTest):
    def test(self):
        absolute_error = abs(self.openfisca_uk - self.official)
        relative_error = absolute_error / self.official
        return relative_error < self.max_error

    def describe(self):
        return f"OpenFisca-UK {self.variable_label} {self.statistic} relative error is less than {self.max_error:,} in {self.year}"


tests = []

for variable in statistics:
    variable_tests = statistics[variable]["test"]
    test_names = list(
        map(
            lambda item: item
            if isinstance(item, str)
            else list(item.keys())[0],
            variable_tests,
        )
    )
    dict_tests = {
        list(item.keys())[0]: item
        for item in variable_tests
        if isinstance(item, dict)
    }
    if "closer_than_ukmod" in test_names:
        for statistic in ("aggregate", "caseload"):
            if statistic in statistics[variable]["ukmod"]:
                for year in statistics[variable]["ukmod"][statistic]:
                    tests += [CloserThanUKMOD(variable, statistic, year)]
    if "aggregate_error_less_than" in test_names:
        for statistic in ("aggregate", "caseload"):
            if statistic in statistics[variable]["official"]:
                for year in statistics[variable]["official"][statistic]:
                    tests += [
                        AbsoluteErrorLessThan(
                            variable,
                            statistic,
                            year,
                            max_error=dict_tests["aggregate_error_less_than"][
                                "aggregate_error_less_than"
                            ],
                        )
                    ]
    if "relative_error_less_than" in test_names:
        for statistic in ("aggregate", "caseload"):
            if statistic in statistics[variable]["official"]:
                for year in statistics[variable]["official"][statistic]:
                    tests += [
                        RelativeErrorLessThan(
                            variable,
                            statistic,
                            year,
                            max_error=dict_tests["relative_error_less_than"][
                                "relative_error_less_than"
                            ],
                        )
                    ]


@pytest.mark.parametrize("test", tests, ids=str)
def test_statistics(test):
    assert test.test()
