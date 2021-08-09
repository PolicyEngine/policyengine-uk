from re import I
from openfisca_uk.situation_examples.examples import single_person_UC
from typing import List
from openfisca_uk.api import *
from openfisca_uk.graphs.data import get_wide_reform_individual_data
from openfisca_uk.graphs.general import (
    formalise_column_names,
    COLORS,
)
import plotly.express as px


def budget_chart(
    reforms: List[Reform],
    names: List[str] = None,
    variables: List[str] = ["household_net_income"],
    situation_function: Callable = single_person_UC,
    return_df: bool = False,
    **kwargs
):
    """Generates a plot of the budget changes for a list of reforms.

    Args:
        reforms (List[Reform]): A list of reform classes.
        names (List[str], optional): The reform names, if multiple reforms are provided.
        variables (List[str], optional): The variables to include in the budget lines. Defaults to ["household_net_income"].
        situation_function (Callable, optional): A function adding situational data to an IndividualSim. Defaults to single_person_UC.
        return_df (bool, optional): Whether to return the data used for the plots. Defaults to False.
        kwargs: Keyword arguments passed to fig.update_layout.

    Returns:
        Figure: The Plotly figure.
    """

    if not isinstance(reforms, list):
        reforms = [reforms]
        names = ["Reform"]

    df = get_wide_reform_individual_data(
        reforms,
        names,
        variables,
        situation_function,
        include_derivatives=False,
    )
    df, column_map = formalise_column_names(df)
    fig = px.line(
        df,
        x=column_map["employment_income"],
        y=[
            column_map[x]
            for x in column_map
            if ("baseline" in x or "reform" in x) and "deriv" not in x
        ],
        animation_frame="Reform",
        color_discrete_sequence=COLORS,
    )
    fig.update_layout(
        legend_title="Source",
    )
    fig.update_layout(**kwargs)
    if return_df:
        return fig, df
    return fig


INVERTED_DERIV_VARIABLES = (
    "household_net_income",
    "net_income",
    "benefits",
    "universal_credit",
)


def mtr_chart(
    reforms: List[Reform],
    names: List[str] = None,
    variables: List[str] = ["household_net_income"],
    situation_function: Callable = single_person_UC,
    invert: List[str] = [],
    derivatives: bool = False,
    return_df: bool = False,
    **kwargs
):
    """Generates a plot of the marginal tax rates for given reforms on a scenario.

    Args:
        reforms (Union[Reform, List[Reform]]): The reforms (multiple reforms creates a slider).
        names (List[str], optional): The reform names, if multiple reforms are provided.
        variables (List[str], optional): The variables to include MTRs or derivatives for, useful for explainable outputs. Defaults to ["household_net_income"].
        situation_function (Callable, optional): A function adding situational data to an IndividualSim. Defaults to single_person_UC.
        invert (List[str], optional): A list of variables that should be inverted to become a 'tax' from a derivative - e.g. NI should not be inverted, but benefits should. Defaults to [].
        derivatives (bool, optional): Whether to plot derivatives or MTRs. The difference is that in an MTR plot, higher values mean higher net incomes, but this isn't true for a derivative plot. Defaults to False.
        return_df (bool, optional): Whether the return the data used to generate the plot. Defaults to False.
        kwargs: Keyword arguments passed to fig.update_layout.

    Returns:
        Figure: The Plotly figure.
    """

    if not isinstance(reforms, list):
        reforms = [reforms]
        names = ["Reform"]

    test_sim = IndividualSim()
    situation_function(test_sim)
    situation_data = test_sim.situation_data
    households = situation_data["households"]
    adults = households[list(households.keys())[0]]["adults"]
    primary_adult = adults[0]

    invert += INVERTED_DERIV_VARIABLES
    df = get_wide_reform_individual_data(
        reforms,
        names,
        variables,
        situation_function,
        primary_adult_name=primary_adult,
        include_derivatives=True,
    )
    for var in df.columns:
        if not derivatives and (
            var.replace("baseline_", "")
            .replace("reform_", "")
            .replace("_deriv", "")
            in invert
        ):
            df[var] = -df[var]
            if df[var].min() < 0 and df[var].max() <= 0:
                df[var] += 1

    df.drop(
        [
            col
            for col in df.columns
            if (
                (("baseline_" in col) or ("reform_" in col))
                and ("deriv" not in col)
            )
        ],
        axis=1,
        inplace=True,
    )

    df, column_map = formalise_column_names(df)
    fig = px.line(
        df,
        x=column_map["employment_income"],
        y=[
            column_map[x]
            for x in column_map
            if ("baseline" in x or "reform" in x) and "deriv" in x
        ],
        animation_frame="Reform",
        color_discrete_sequence=COLORS,
    )
    fig.update_layout(legend_title="Source", yaxis_tickformat="%")
    fig.update_layout(**kwargs)
    if return_df:
        return fig, df
    return fig
