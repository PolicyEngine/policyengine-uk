from typing import Union
import yaml
from pathlib import Path
from openfisca_uk import Microsimulation
from openfisca_uk_data import FRSEnhanced
import pytest

with open(Path(__file__).parent / "statistics.yaml") as f:
    statistics = yaml.load(f, Loader=yaml.SafeLoader)

sim = Microsimulation(dataset=FRSEnhanced, year=2019)
variables = sim.simulation.tax_benefit_system.variables
parameters = sim.simulation.tax_benefit_system.parameters


def get_openfisca_uk_aggregate(variable: str, year: int) -> float:
    return sim.calc(variable, period=year, map_to="household").sum()


def get_openfisca_uk_caseload(variable: str, year: int) -> float:
    values = sim.map_to(
        sim.calc(variable, period=year).values > 0,
        variables[variable].entity.key,
        "household",
    )
    return (sim.calc("household_weight", period=year).values * values).sum()


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
        try:
            if self.statistic == "aggregate":
                return statistics[self.variable][source]["aggregate"][
                    self.year
                ]
            elif self.statistic == "caseload":
                return statistics[self.variable][source]["count"][self.year]
        except:
            # Not overridden - use statistics parameter
            if source == "official":
                return parameters.calibration.children[
                    {"aggregate": "aggregate", "caseload": "count"}[
                        self.statistic
                    ]
                ].children[self.variable](f"{self.year}-01-01")
            elif source == "ukmod":
                raise ValueError(
                    f"UKMOD values not given for {self.variable} {self.statistic} in {self.year}"
                )
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
        return openfisca_uk_error <= ukmod_error, locals()

    def describe(self):
        return f"OpenFisca-UK {self.variable_label} {self.statistic} at least as close to the official aggregate as UKMOD in {self.year}"


class AbsoluteErrorLessThan(StatisticTest):
    def test(self):
        openfisca_uk = self.openfisca_uk
        official = self.official
        openfisca_uk_error = abs(openfisca_uk - official)
        return openfisca_uk_error < self.max_error, locals()

    def describe(self):
        return f"OpenFisca-UK {self.variable_label} {self.statistic} error is less than {self.max_error:,} in {self.year}"


class RelativeErrorLessThan(StatisticTest):
    def test(self):
        openfisca_uk = self.openfisca_uk
        official = self.official
        absolute_error = abs(openfisca_uk - official)
        relative_error = absolute_error / official
        return relative_error < self.max_error, locals()

    def describe(self):
        return f"OpenFisca-UK {self.variable_label} {self.statistic} error is less than {self.max_error:.1%} in {self.year}"


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
    for statistic in ("aggregate", "caseload"):
        if f"{statistic}_closer_than_ukmod" in test_names:
            if statistic in statistics[variable]["ukmod"]:
                for year in statistics[variable]["ukmod"][statistic]:
                    tests += [CloserThanUKMOD(variable, statistic, year)]
        if f"{statistic}_error_less_than" in test_names:
            for year in range(2019, 2023):
                tests += [
                    AbsoluteErrorLessThan(
                        variable,
                        statistic,
                        year,
                        max_error=dict_tests[
                            f"absolute_{statistic}_error_less_than"
                        ][f"absolute_{statistic}_error_less_than"],
                    )
                ]
        if f"relative_{statistic}_error_less_than" in test_names:
            for year in range(2019, 2023):
                tests += [
                    RelativeErrorLessThan(
                        variable,
                        statistic,
                        year,
                        max_error=dict_tests[
                            f"relative_{statistic}_error_less_than"
                        ][f"relative_{statistic}_error_less_than"],
                    )
                ]


@pytest.mark.parametrize("test", tests, ids=str)
def test_statistics(test):
    passed, variables = test.test()
    assert passed, "Test failed: \n\n" + "\n".join(
        [f"{key}: {value}" for key, value in variables.items()]
    )
