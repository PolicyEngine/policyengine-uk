import re
from policyengine_uk.system import system
import plotly.express as px
import pandas as pd
from plotly import graph_objects as go


def find_variable_in_trees(variable_name, tracer):
    for tree in tracer.trees:
        try:
            node = find_variable_in_tree_recursive(variable_name, tree)
            if node:
                return node
        except ValueError:
            continue  # Variable not in this tree, try next

    raise ValueError(
        f"Variable '{variable_name}' not found in any simulation tree. "
        f"Make sure you've calculated this variable or a parent variable that depends on it."
    )


def find_variable_in_tree_recursive(variable_name, node):
    if node.name == variable_name:
        return node

    for child in node.children:
        result = find_variable_in_tree_recursive(variable_name, child)
        if result:
            return result

    return None


def get_variable_dependencies(variable_name, sim):
    node = find_variable_in_trees(variable_name, sim.tracer)
    if not node:
        return []
    return [child.name for child in node.children]


def extract_variables_regex(formula_source):
    # Find all strings in double quotes that look like variable names
    pattern = r'benunit\(\s*["\']([^"\']+)["\']\s*,'
    matches = re.findall(pattern, formula_source)
    return matches


def calculate_dependency_contributions(
    sim, variable_name, year, top_n=None, filter=None, map_to=None
):
    original_values = sim.calculate(variable_name, year)

    if map_to is not None:
        source_entity = sim.tax_benefit_system.get_variable(
            variable_name
        ).entity.key
        original_values_mapped = sim.map_result(
            original_values,
            source_entity,
            map_to,
        )
    else:
        original_values_mapped = original_values

    dependency_contributions = {}
    first_level_dependencies = get_variable_dependencies(variable_name, sim)
    for variable in first_level_dependencies:
        if "weight" in variable:
            continue
        sim.get_holder(variable_name).delete_arrays(year)
        value_type = system.get_variable(variable).value_type
        current_values = sim.calculate(variable, year)
        if value_type == float:
            sim.set_input(variable, year, (current_values * 0).astype(float))

        new_values_mapped = sim.calculate(variable_name, year, map_to=map_to)
        if filter is not None:
            contribution = (
                original_values_mapped[filter] - new_values_mapped[filter]
            ).mean()
        else:
            contribution = (original_values_mapped - new_values_mapped).mean()
        dependency_contributions[variable] = contribution
        sim.set_input(variable_name, year, original_values)
        sim.set_input(variable, year, current_values)

    result = pd.Series(dependency_contributions)

    if top_n is not None:
        # Keep the top N variables by absolute contribution
        result = result.reindex(result.abs().nlargest(top_n).index)

    return result.sort_values(ascending=False)


def calculate_dependency_contribution_change(
    baseline_sim, reform_sim, variable_name, year, reform_year=None, top_n=5
):
    baseline_dependency = calculate_dependency_contributions(
        baseline_sim, variable_name, year
    )
    reform_dependency = calculate_dependency_contributions(
        reform_sim, variable_name, reform_year or year
    )

    df = pd.DataFrame(
        {
            "baseline": pd.Series(baseline_dependency),
            "reform": pd.Series(reform_dependency),
        }
    ).fillna(0)

    df["change"] = df["reform"] - df["baseline"]
    df["relative_change"] = df["change"] / df["baseline"].abs().replace(0, 1)

    # Keep the top N variables by absolute change
    if top_n is not None:
        df = df.reindex(df["change"].abs().nlargest(top_n).index)

    return df.sort_values(by="change", ascending=False)


def create_waterfall_chart(sim, variable_name, year, top_n=5):
    if not sim.trace:
        raise ValueError(
            "Simulation must have trace enabled to create a waterfall chart."
        )

    df = calculate_dependency_contributions(
        sim, variable_name, year, top_n=top_n
    )

    # make a waterfall chart

    fig = go.Figure(
        go.Waterfall(
            name="Waterfall",
            orientation="v",
            measure=["relative"] * len(df),
            x=df.index,
            y=df.values,
            connector={"line": {"color": "rgb(63, 63, 63)", "width": 2}},
            increasing={"marker": {"color": "green"}},
            decreasing={"marker": {"color": "red"}},
            totals={"marker": {"color": "blue"}},
        )
    )
    return format_fig(fig).update_layout(
        title=f"Dependency contributions for {variable_name} in {year}",
    )


def create_waterfall_change_chart(
    sim_1, sim_2, variable_name, year, sim_2_year=None, top_n=5
):
    df = calculate_dependency_contribution_change(
        sim_1, sim_2, variable_name, year, reform_year=sim_2_year, top_n=top_n
    )

    # make a waterfall chart

    fig = go.Figure(
        go.Waterfall(
            name="Waterfall",
            orientation="v",
            measure=["relative"] * len(df),
            x=df.index,
            y=df.change,
            connector={"line": {"color": "rgb(63, 63, 63)", "width": 2}},
            increasing={"marker": {"color": "green"}},
            decreasing={"marker": {"color": "red"}},
            totals={"marker": {"color": "blue"}},
        )
    )
    return format_fig(fig).update_layout(
        title=f"Change in {variable_name} contributions from reform",
    )


def add_fonts():
    fonts = HTML(
        """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:ital,opsz,wght@0,8..144,100..900;1,8..144,100..900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet">
    """
    )
    return display_html(fonts)


from IPython.core.display import HTML, display_html


def format_fig(fig):
    # PolicyEngine style (roboto mono for numbers, roboto serif for text), dark grey for negative, blue for positive, spacing, etc.

    # Set layout properties for a clean, professional look
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Roboto Serif",
        font_size=12,
        margin=dict(l=60, r=60, t=80, b=60),
        title_font_size=16,
        title_font_family="Roboto Serif",
        title_x=0.5,
        title_xanchor="center",
    )

    # Update axes
    fig.update_xaxes(
        title_font_family="Roboto Serif",
        tickfont_family="Roboto Mono",
        showline=True,
        linewidth=1,
        linecolor="lightgray",
    )

    fig.update_yaxes(
        title_font_family="Roboto Serif",
        tickfont_family="Roboto Mono",
        tickformat=",.0f",
        tickprefix="£",
        gridcolor="lightgray",
        showline=True,
        linewidth=1,
        linecolor="lightgray",
    )

    # Update waterfall specific styles
    fig.update_traces(
        increasing=dict(marker=dict(color="#2C6496")),
        decreasing=dict(marker=dict(color="#555555")),
        connector=dict(line=dict(color="rgb(63, 63, 63)", width=1)),
    )

    # Height/width adjustments for better visibility
    fig.update_layout(
        height=600,
        width=800,
        # set font to black
        font_color="black",
    )

    # Add rounded numbers on bars
    for trace in fig.data:
        if isinstance(trace, go.Waterfall):
            trace.texttemplate = "£%{y:,.0f}"
            trace.textposition = "outside"
            trace.hovertemplate = "%{x}: £%{y:,.0f}<extra></extra>"
            # mono font for numbers
            trace.textfont = dict(family="Roboto Mono", size=12, color="black")

    # Add padding round the edges
    fig.update_layout(margin=dict(l=100, r=100, t=100, b=100))

    return fig


add_fonts()
