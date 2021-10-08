from typing import Callable, List
from openfisca_core.parameters.parameter import Parameter
from openfisca_core.parameters.parameter_scale import ParameterScale
import pytest
from openfisca_uk import Microsimulation
from openfisca_uk.reforms.tools.parametric import set_parameter


def collect_parameters(sim: Microsimulation) -> List[Parameter]:
    parameters = []
    for (
        parameter
    ) in sim.simulation.tax_benefit_system.parameters.get_descendants():
        if isinstance(parameter, Parameter):
            parameters += [parameter]
        elif isinstance(parameter, ParameterScale):
            for bracket in parameter.brackets:
                for attribute in ("rate", "amount", "threshold"):
                    if hasattr(bracket, attribute):
                        parameters += [getattr(bracket, attribute)]
    return parameters


def generate_tests(sim: Microsimulation) -> Callable:
    parameters = collect_parameters(sim)

    @pytest.mark.parametrize(
        "parameter",
        parameters,
        ids=[parameter.name for parameter in parameters],
    )
    def test_parameter(parameter):
        if hasattr(parameter, "metadata") and "tests" in parameter.metadata:
            for test in parameter.metadata["tests"]:
                if "period" not in test:
                    test["period"] = 2021
                reform = set_parameter(parameter.name, test["value"])
                if "revenue" in test:
                    revenue = (
                        -type(sim)(reform, dataset=sim.dataset)
                        .calc("net_income", period=test["period"])
                        .sum()
                        + sim.calc("net_income", period=test["period"]).sum()
                    )
                    if "min" in test["revenue"]:
                        assert revenue >= test["revenue"]["min"]
                    if "max" in test["revenue"]:
                        assert revenue <= test["revenue"]["max"]
                    if "positive" in test["revenue"]:
                        assert revenue > 0
                    if "negative" in test["revenue"]:
                        assert revenue < 0
                if "poverty_effect" in test:
                    poverty_effect = (
                        type(sim)(reform, dataset=sim.dataset)
                        .calc(
                            "in_poverty_bhc",
                            period=test["period"],
                            map_to="person",
                        )
                        .mean()
                        / sim.calc(
                            "in_poverty_bhc",
                            period=test["period"],
                            map_to="person",
                        ).mean()
                        - 1
                    )
                    if "min" in test["poverty_effect"]:
                        assert poverty_effect >= test["poverty_effect"]["min"]
                    if "max" in test["poverty_effect"]:
                        assert poverty_effect <= test["poverty_effect"]["max"]
                    if "positive" in test["poverty_effect"]:
                        assert poverty_effect > 0
                    if "negative" in test["poverty_effect"]:
                        assert poverty_effect < 0

    return test_parameter


test_parameter = generate_tests(Microsimulation())
