from typing import Callable, List, Tuple
from openfisca_core.parameters.parameter import Parameter
from openfisca_core.parameters.parameter_scale import ParameterScale
from openfisca_uk_data import FRS
import pytest
from openfisca_uk import Microsimulation
from openfisca_uk.reforms.tools.parametric import set_parameter


def collect_tests(sim: Microsimulation) -> List[Tuple[Parameter, dict]]:
    parameters = []
    tests = []
    test_numbers = []
    for (
        parameter
    ) in sim.simulation.tax_benefit_system.parameters.get_descendants():
        if isinstance(parameter, Parameter):
            if (
                hasattr(parameter, "metadata")
                and "tests" in parameter.metadata
            ):
                i = 0
                for test in parameter.metadata["tests"]:
                    parameters += [parameter]
                    tests += [test]
                    test_numbers += [i]
                    i += 1
        elif isinstance(parameter, ParameterScale):
            for bracket in parameter.brackets:
                for attribute in ("rate", "amount", "threshold"):
                    if hasattr(bracket, attribute):
                        param = getattr(bracket, attribute)
                        if (
                            hasattr(param, "metadata")
                            and "tests" in param.metadata
                        ):
                            i = 0
                            for test in param.metadata["tests"]:
                                parameters += [param]
                                tests += [test]
                                test_numbers += [i]
                                i += 1
    return parameters, tests, test_numbers


def generate_tests(sim: Microsimulation) -> Callable:
    parameters, tests, indices = collect_tests(sim)

    @pytest.mark.parametrize(
        "parameter, test",
        zip(parameters, tests),
        ids=[
            f"{parameter.name}-{number}"
            for parameter, number in zip(parameters, indices)
        ],
    )
    def test_parameter(parameter, test):
        if "period" not in test:
            test["period"] = 2021
        if "value" in test:
            reform = set_parameter(parameter.name, test["value"])
            reformed = type(sim)(
                (sim.reforms, reform), dataset=sim.dataset, year=sim.year
            )
        if "revenue" in test:
            baseline_net_income = sim.calc(
                "net_income", period=test["period"]
            ).sum()
            reformed_net_income = reformed.calc(
                "net_income", period=test["period"]
            ).sum()
            revenue = baseline_net_income - reformed_net_income
            if "min" in test["revenue"]:
                assert revenue >= test["revenue"]["min"]
            if "max" in test["revenue"]:
                assert revenue <= test["revenue"]["max"]
            if "positive" in test["revenue"]:
                assert revenue > 0
            if "negative" in test["revenue"]:
                assert revenue < 0
        if "poverty_effect" in test:
            # type(sim) ensures we instantiate the same class
            baseline_poverty = sim.calc(
                "in_poverty_bhc",
                period=test["period"],
                map_to="person",
            ).mean()
            reformed_poverty = reformed.calc(
                "in_poverty_bhc",
                period=test["period"],
                map_to="person",
            ).mean()
            poverty_effect = reformed_poverty / baseline_poverty - 1
            if "min" in test["poverty_effect"]:
                assert poverty_effect >= test["poverty_effect"]["min"]
            if "max" in test["poverty_effect"]:
                assert poverty_effect <= test["poverty_effect"]["max"]
            if "positive" in test["poverty_effect"]:
                assert poverty_effect > 0
            if "negative" in test["poverty_effect"]:
                assert poverty_effect < 0
        if "increases_net_income" in test:
            reform = set_parameter(
                parameter.name, parameter(test["period"]) * 1.01 + 1e-2
            )
            reformed = type(sim)(
                (sim.reforms, reform), dataset=sim.dataset, year=sim.year
            )
            assert (
                reformed.calc("net_income", map_to="household")
                - sim.calc("net_income", map_to="household")
                >= 0
            ).all()
        if "decreases_net_income" in test:
            reform = set_parameter(
                parameter.name, parameter(test["period"]) * 1.01 + 1e-2
            )
            reformed = type(sim)(
                (sim.reforms, reform), dataset=sim.dataset, year=sim.year
            )
            assert (
                reformed.calc("net_income", map_to="household")
                - sim.calc("net_income", map_to="household")
                <= 0
            ).all()

    return test_parameter


test_parameter = generate_tests(Microsimulation(dataset=FRS, year=2019))
