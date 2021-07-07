from typing import List, Union
import plotly.express as px
from openfisca_uk.api import *
import pandas as pd
from microdf import MicroSeries
from functools import wraps
from openfisca_uk.graphs.general import net_cost


def _get_group_reduction(
    incomes: MicroSeries,
    baseline_values: MicroSeries,
    reform_values: MicroSeries,
    bucket: str,
    aggregation: str,
    compare_groups: bool,
    relative: bool,
):
    reduction_function = lambda values: values.groupby(
        incomes.__getattribute__(f"{bucket}_rank")()
    ).__getattribute__(aggregation)()
    if compare_groups:
        change = reduction_function(reform_values) - reduction_function(
            baseline_values
        )
        if relative:
            change /= reduction_function(incomes)
    else:
        if not relative:
            change = reduction_function(reform_values - baseline_values)
        else:
            change = reduction_function(
                (reform_values - baseline_values) / incomes
            )
    return change


def distributional_chart(
    incomes: MicroSeries,
    baseline_values: MicroSeries,
    reform_values: Union[MicroSeries, List[MicroSeries]],
    reform_names: list = None,
    bucket: str = "decile",
    value_label: str = "net income",
    aggregation: str = "mean",
    compare_groups: bool = "true",
    relative: bool = False,
    currency: str = "£",
    include_all_ticks: bool = True,
    **kwargs,
):
    """Generates a Plotly bar chart for changes to a variable based on quantiles.

    Args:
        incomes (MicroSeries): Baseline incomes (or any variable to group by quantile on).
        baseline_values (MicroSeries): Baseline y-values.
        reform_values (Union[MicroSeries, List[MicroSeries]]): Reform y-values, or a list of arrays to create an animation frame.
        reform_names (list, optional): Names of reforms.
        bucket (str, optional): The type of quantile grouping (quintile, decile, percentile). Defaults to "decile".
        value_label (str, optional): The name of the value variable. Defaults to "net income".
        aggregation (str, optional): The type of aggregation (mean, sum, median). Defaults to "mean".
        compare_groups (bool, optional): Whether to compare group aggregates (true) or aggregate individual comparisons (false).
        relative (bool, optional): Whether changes should be a percentage of their baseline value.
        currency (str, optional): The currency format to use if using absolute changes.
        **kwargs (dict): Any additional arguments to pass to fig.update_layout (e.g. title=...).

    Returns:
        Figure: The Plotly figure.
    """
    assert bucket in (
        "quintile",
        "decile",
        "percentile",
    ), "Unrecognised bucketing type"
    assert aggregation in (
        "mean",
        "sum",
        "median",
    ), "Unrecognised aggregation type"

    if isinstance(reform_values, list) and not reform_names:
        reform_names = [
            f"Reform {i}" for i in range(1, len(reform_values) + 1)
        ]

    x_label = f"Income {bucket}"
    y_label = f"Change to {value_label}"

    reduction_func = lambda reform_values: _get_group_reduction(
        incomes,
        baseline_values,
        reform_values,
        bucket,
        aggregation,
        compare_groups,
        relative,
    )

    if isinstance(reform_values, list):
        change = list(map(reduction_func, reform_values))
        names = np.repeat(reform_names, len(change[0]))
        change = pd.concat(change)
    else:
        change = reduction_func(reform_values)
        names = None

    data = pd.DataFrame(
        {
            x_label: change.index,
            y_label: change.values,
        }
    )
    if names is not None:
        data["Reform"] = names
        fig = px.bar(data, x=x_label, y=y_label, animation_frame="Reform")
    else:
        fig = px.bar(data, x=x_label, y=y_label)
    if relative:
        fig.update_layout(yaxis_tickformat="%")
    else:
        fig.update_layout(yaxis_tickprefix=currency)
    if include_all_ticks:
        numbers = dict(quartile=4, quintile=5, decile=10, percentile=100)[
            bucket
        ]
        if numbers <= 10:
            ticks = list(range(1, numbers + 1))
        else:
            ticks = None
        fig.update_layout(xaxis_tickvals=ticks)
    fig.update_layout(**kwargs)
    return fig


# Bucket-specific shortcut functions

quartile_plot = wraps(distributional_chart)(
    lambda *args, **kwargs: distributional_chart(
        *args, bucket="quartile", **kwargs
    )
)
quintile_plot = wraps(distributional_chart)(
    lambda *args, **kwargs: distributional_chart(
        *args, bucket="quintile", **kwargs
    )
)
decile_plot = wraps(distributional_chart)(
    lambda *args, **kwargs: distributional_chart(
        *args, bucket="decile", **kwargs
    )
)
percentile_plot = wraps(distributional_chart)(
    lambda *args, **kwargs: distributional_chart(
        *args, bucket="percentile", **kwargs
    )
)


def waterfall_data(
    reforms: List[Reform],
    reform_labels: List[str],
    subreform_labels: List[str],
    baseline: Microsimulation = None,
    **kwargs,
):
    """Generates data for a waterfall funding breakdown chart.

    Args:
        reforms (List[Reform]): A list of reforms to show funding breakdowns for. Each reform must have the same top-level subreforms.
        reform_labels (List[str]): The names of the reforms.
        subreform_labels (List[str]): The names of the components of the reforms.
        baseline (Microsimulation, optional): A baseline simulation - can improve speed if already initialised. Defaults to None.

    Returns:
        pd.DataFrame: The waterfall plot dataframe.
    """
    baseline = baseline or Microsimulation(**kwargs)
    dfs = []
    for reform, name in zip(reforms, reform_labels):
        net_costs = []
        for i in range(len(reform) + 1):
            net_costs += [
                net_cost(baseline, Microsimulation(reform[:i], **kwargs))
            ]
        net_costs = np.array(net_costs)
        labels = subreform_labels + ["Remaining"]
        resulting_costs = pd.Series(net_costs[1:] - net_costs[:-1])
        resulting_costs = pd.Series(list(resulting_costs) + [net_costs[-1]])
        if net_costs[-1] < 0:
            final_base = 0
        else:
            final_base = -net_costs[-1]
        breakdown = pd.DataFrame(
            dict(
                # Each component has white below it, so double the records.
                component=labels * 2,
                amount=[0]
                + list(-resulting_costs.cumsum()[1:-1])
                + [final_base]
                + list(resulting_costs.abs()),
                Type=["-"] * len(labels)
                + np.where(
                    resulting_costs < 0, "Revenue", "Spending"
                ).tolist(),
                Reform=name,
            )
        )
        dfs += [breakdown]
    return pd.concat(dfs)


SPENDING_COLOR = "#BDBDBD"
REVENUE_COLOR = "#1976D2"


def waterfall_chart(
    reforms: List[Reform],
    subreform_labels: List[str],
    reform_labels: List[str] = None,
    baseline: Microsimulation = None,
):
    """Generates a waterfull funding breakdown plot.

    Args:
        reforms (Union[Reform, List[Reform]]): A list of reforms - each must have the same top-level subreforms.
        subreform_labels (List[str]): The names of the top-level reform components.
        reform_labels (List[str], optional): The names of the reforms, if multiple are provided.
        baseline (Microsimulation, optional): A baseline simulation - can improve speed if pre-initialised. Defaults to None.

    Returns:
        Figure: The Plotly figure.
    """
    if not isinstance(reforms, list):
        reforms = [reforms]
        reform_labels = ["Reform"]

    return px.bar(
        waterfall_data(
            reforms, reform_labels, subreform_labels, baseline=baseline
        ),
        x="component",
        y="amount",
        color="Type",
        barmode="stack",
        animation_frame="Reform",
        color_discrete_sequence=["white", REVENUE_COLOR, SPENDING_COLOR],
    ).update_layout(
        xaxis_title="Component",
        yaxis_title="Surplus",
        yaxis_tickprefix="£",
        legend_title="",
        # White background to match the unaffected area.
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
