from typing import Callable, List
from openfisca_uk.api import *
from openfisca_uk.situation_examples.examples import single_person_UC
import pandas as pd


def get_wide_reform_population_data(
    reforms: List[Reform],
    names: List[str],
    variables: List[str] = [],
    mapping: str = "person",
    function: Callable = None,
    **kwargs,
) -> pd.DataFrame:
    """Generates wide-form data from given reforms and variable names
    (e.g. for creating animation frames for Plotly graphs).

    Args:
        reforms (List[Reform]): A list of Reform classes.
        names (List[str]): A list of variable names to calculate for each reform
        variables (List[str], optional): A list of variable names to calculate of each reform.
        mapping (person): The mapping to apply to each calculation (person, benunit, household).
        function (Callable[(baseline, reform_sim) -> pd.DataFrame]): A function to apply instead of calculating variables.
        kwargs: Keywork arguments passed to Microsimulations.
    Returns:
        pd.DataFrame: A DataFrame with each row containing:
        {reform: name, baseline_first_variable_name: [...],
        reform_first_variable_name: [...], ...}
    """
    dfs = []
    baseline = Microsimulation(**kwargs)
    for reform, name in zip(reforms, names):
        reform_sim = Microsimulation(reform, **kwargs)
        df = pd.DataFrame()
        if function is None:
            for variable in variables:
                df[f"reform_{variable}"] = reform_sim.calc(
                    variable, map_to=mapping
                )
                df[f"baseline_{variable}"] = baseline.calc(
                    variable, map_to=mapping
                )
                df["Reform"] = name
                df["weight"] = baseline.calc(f"{mapping}_weight")
        else:
            df = function(baseline, reform_sim)
            df["Reform"] = name
        dfs += [df]
    df = pd.concat(dfs)
    return df


def get_wide_reform_individual_data(
    reforms: List[Reform],
    names: List[str],
    variables: List[str] = ["net_income"],
    situation_function: Callable = single_person_UC,
    varying: str = "employment_income",
    vary_min: float = 0,
    vary_max: float = 200000,
    vary_step: float = 100,
    include_derivatives: bool = True,
    primary_adult_name: str = "adult",
    **kwargs,
):
    """Generates wide-format individual data from a set of reforms, varying a
    variable (a row for each reform-input value-other values set).

    Args:
        reforms (List[Reform]): A list of reforms.
        names (List[str]): The corresponding reform names.
        variables (List[str], optional): The variables to include. Defaults to ["net_income"].
        situation_function (Callable, optional): A function adding situational data to the simulation.
            Defaults to single_person_UC.
        varying (str, optional): The variable to vary (e.g. employment income). Defaults to
            "employment_income".
        vary_min (float, optional): The starting value of the varying variable. Defaults to 0.
        vary_max (float, optional): The ending value of the varying variable. Defaults to 200,000.
        vary_step (float, optional): The interval of the varying variable. Defaults to 100.
        include_derivatives (bool, optional): Whether to include derivatives for each
            calculation. Defaults to True.
        primary_adult_name (str, optional): The name of the adult to calculate derivatives
            for. Defaults to "adult".
        kwargs: Keyword arguments passed to Microsimulations.

    Returns:
        pd.DataFrame: The resulting dataframe.
    """
    baseline = IndividualSim(**kwargs)
    baseline = situation_function(baseline)
    baseline.vary(varying)
    dfs = []
    for reform, name in zip(reforms, names):
        df = pd.DataFrame()
        reform_sim = IndividualSim(reform, **kwargs)
        reform_sim = situation_function(reform_sim)
        reform_sim.vary(varying, min=vary_min, max=vary_max, step=vary_step)
        df[varying] = baseline.calc(varying)[0]
        for variable in variables:
            try:
                df[f"baseline_{variable}"] = baseline.calc(variable).sum(
                    axis=0
                )
                if include_derivatives:
                    df[f"baseline_{variable}_deriv"] = baseline.deriv(
                        variable,
                        wrt=varying,
                        var_target=primary_adult_name,
                        wrt_target=primary_adult_name,
                    )
            except:
                df[f"baseline_{variable}"] = np.zeros_like(df[varying])
                if include_derivatives:
                    df[f"baseline_{variable}_deriv"] = np.zeros_like(
                        df[varying]
                    )
            df[f"reform_{variable}"] = reform_sim.calc(variable).sum(axis=0)
            if include_derivatives:
                df[f"reform_{variable}_deriv"] = reform_sim.deriv(
                    variable,
                    wrt=varying,
                    var_target=primary_adult_name,
                    wrt_target=primary_adult_name,
                )
            df[f"reform"] = name
        dfs += [df]
    df = pd.concat(dfs)
    return df
