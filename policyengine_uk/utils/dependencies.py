import re
import numpy as np
from policyengine_core import periods
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


def index_calculations(tracer):
    """The trace node of each calculation, by (variable, period, branch name).

    A variable read again after it was calculated gets a node without
    children, so the index keeps the first node with children: the one that
    shows what the calculation read.
    """
    index = {}
    stack = list(reversed(tracer.trees))
    while stack:
        node = stack.pop()
        if node.children:
            key = (node.name, periods.period(node.period), node.branch_name)
            index.setdefault(key, node)
            stack.extend(reversed(node.children))
    return index


def find_calculation(variable_name, period, sim, index):
    # The node of variable_name's calculation over period: on sim's branch,
    # else on the nearest ancestor (a branch reads the values its ancestors
    # calculated), else on any branch, else the first node of variable_name
    # over any period.
    period = periods.period(period)
    ancestor = sim
    while ancestor is not None:
        node = index.get((variable_name, period, ancestor.branch_name))
        if node is not None:
            return node
        ancestor = getattr(ancestor, "parent_branch", None)
    for (name, node_period, _), node in index.items():
        if name == variable_name and node_period == period:
            return node
    return find_variable_in_trees(variable_name, sim.tracer)


def get_dependency_nodes(node, index=None):
    # A variable calculated over a period other than its definition period (a
    # monthly one summed over a year, or a yearly one divided into a month)
    # has itself as a child on the same branch for each period it is
    # calculated over; what it reads is under those children. A child that
    # read a value already stored has no children of its own, so index (from
    # index_calculations) gives the calculation that stored it. The variable
    # read on another branch is a dependency, as is the variable read over a
    # period that neither contains nor is contained in its own.
    nodes = []
    node_period = periods.period(node.period)
    for child in node.children:
        child_period = periods.period(child.period)
        if (
            child.name == node.name
            and child.branch_name == node.branch_name
            and (
                node_period.contains(child_period) or child_period.contains(node_period)
            )
        ):
            if not child.children and index is not None:
                child = index.get((child.name, child_period, child.branch_name), child)
            nodes.extend(get_dependency_nodes(child, index))
        else:
            nodes.append(child)
    return nodes


def get_variable_dependencies(variable_name, sim, period=None):
    """The variables variable_name reads directly, from sim's trace.

    With period, those its calculation over period read; otherwise those of
    the first calculation of variable_name the trace shows.
    """
    if period is None:
        node = find_variable_in_trees(variable_name, sim.tracer)
        if not node:
            return []
        return [child.name for child in get_dependency_nodes(node)]
    index = index_calculations(sim.tracer)
    node = find_calculation(variable_name, period, sim, index)
    return [child.name for child in get_dependency_nodes(node, index)]


def get_direct_reads(variable_name, sim, period):
    """The periods variable_name, calculated over period, read each variable
    over on its own branch: a dict from variable name to periods, from sim's
    trace."""
    index = index_calculations(sim.tracer)
    node = find_calculation(variable_name, period, sim, index)
    return reads_on_branch(node, get_dependency_nodes(node, index))


def reads_on_branch(node, dependency_nodes):
    # The periods node read each of dependency_nodes over, on its own branch.
    reads = {}
    for child in dependency_nodes:
        if child.branch_name == node.branch_name:
            read_periods = reads.setdefault(child.name, [])
            read_period = periods.period(child.period)
            if read_period not in read_periods:
                read_periods.append(read_period)
    return reads


def definition_periods(variable, read_periods):
    # The periods variable is defined for that make up each read period, or
    # that contain it (the year a month of a yearly variable is in).
    unit = variable.definition_period
    result = []
    for read_period in read_periods:
        if unit == periods.ETERNITY:
            covering = [periods.period(periods.ETERNITY)]
        elif periods.unit_weight(unit) <= periods.unit_weight(read_period.unit):
            covering = read_period.get_subperiods(unit)
        else:
            covering = [
                subperiod.this_year if unit == periods.YEAR else subperiod.first_month
                for subperiod in read_period.get_subperiods(read_period.unit)
            ]
        result.extend(p for p in covering if p not in result)
    return result


def extract_variables_regex(formula_source):
    # Find all strings in double quotes that look like variable names
    pattern = r'benunit\(\s*["\']([^"\']+)["\']\s*,'
    matches = re.findall(pattern, formula_source)
    return matches


def unused_branch_name(sim, base_name="dependency-contribution"):
    # A name no branch of sim, sim itself or its ancestors uses, so get_branch
    # creates a new branch instead of returning an existing one.
    taken = set(sim.branches)
    ancestor = sim
    while ancestor is not None:
        taken.add(ancestor.branch_name)
        ancestor = getattr(ancestor, "parent_branch", None)
    name, suffix = base_name, 1
    while name in taken:
        suffix += 1
        name = f"{base_name}-{suffix}"
    return name


def calculate_with_dependency_zeroed(
    sim, variable_name, dependency, year, map_to=None, reads=None
):
    """Recalculate variable_name over year with dependency zero.

    reads (by default get_direct_reads(variable_name, sim, year)) gives the
    periods variable_name read each variable over. dependency is set to zero
    for each period it is defined for that makes up or contains year or a
    period variable_name read it over. Every other variable variable_name
    read is held at the value sim holds, as an input, so the result is the
    change from dependency alone: on a branch, an input drops the values
    calculated from the one it replaces, which would otherwise be
    recalculated with dependency zero.

    Runs on a new untraced branch of sim, removed from sim.branches before
    returning: what the branch inputs or deletes stays in the branch, so sim
    is left as it was. Inputting each defined period directly means no
    set_input helper has to split an annual value across months that already
    hold values, which core refuses when they do not add up to it.
    """
    period = periods.period(year)
    variables = sim.tax_benefit_system.variables
    if reads is None:
        reads = get_direct_reads(variable_name, sim, period)
    zeroed_reads = [period] + reads.get(dependency, [])
    zeroed = definition_periods(variables[dependency], zeroed_reads)
    held = {
        name: definition_periods(variables[name], read_periods)
        for name, read_periods in reads.items()
        if name not in (dependency, variable_name)
        and not variables[name].is_neutralized
    }
    zeros = np.zeros(sim.get_variable_population(dependency).count)

    branch_name = unused_branch_name(sim)
    branch = sim.get_branch(branch_name)
    try:
        branch.trace = False
        # What sim holds for each held read, taken before the branch changes.
        held_values = {}
        for name, held_periods in held.items():
            holder = branch.get_holder(name)
            for held_period in held_periods:
                value = holder.get_array(held_period, branch.branch_name)
                if value is None:
                    value = branch.calculate(name, held_period)
                held_values[name, held_period] = value
        for zeroed_period in zeroed_reads + zeroed:
            branch.delete_arrays(dependency, zeroed_period)
        for zeroed_period in zeroed:
            branch.set_input(dependency, zeroed_period, zeros)
        for (name, held_period), value in held_values.items():
            branch.set_input(name, held_period, value)
        branch.delete_arrays(variable_name, period)
        return branch.calculate(variable_name, period, map_to=map_to)
    finally:
        sim.branches.pop(branch_name, None)


def calculate_dependency_contributions(
    sim, variable_name, year, top_n=None, filter=None, map_to=None
):
    """Mean change in variable_name from zeroing each variable it reads directly.

    The variables variable_name reads directly in its calculation over year,
    and the periods it reads them over, come from sim's trace, so sim needs
    trace=True. A float one's contribution is the mean of variable_name minus
    variable_name recalculated with that variable zero over year and where
    it was read, and every other variable read held (see
    calculate_with_dependency_zeroed), after mapping to map_to and selecting
    filter if given. So for a target that adds and subtracts what it reads,
    the contributions sum to its mean. Other variables contribute zero. sim's
    values are left unchanged.
    """
    original_values = sim.calculate(variable_name, year)

    if map_to is not None:
        source_entity = sim.tax_benefit_system.get_variable(variable_name).entity.key
        original_values_mapped = sim.map_result(
            original_values,
            source_entity,
            map_to,
        )
    else:
        original_values_mapped = original_values

    dependency_contributions = {}
    index = index_calculations(sim.tracer)
    node = find_calculation(variable_name, year, sim, index)
    dependency_nodes = get_dependency_nodes(node, index)
    first_level_dependencies = [child.name for child in dependency_nodes]
    reads = reads_on_branch(node, dependency_nodes)
    for variable in dict.fromkeys(first_level_dependencies):
        if "weight" in variable:
            continue
        value_type = sim.tax_benefit_system.get_variable(variable).value_type
        if value_type == float:
            new_values_mapped = calculate_with_dependency_zeroed(
                sim, variable_name, variable, year, map_to=map_to, reads=reads
            )
        else:
            new_values_mapped = original_values_mapped
        if filter is not None:
            contribution = (
                original_values_mapped[filter] - new_values_mapped[filter]
            ).mean()
        else:
            contribution = (original_values_mapped - new_values_mapped).mean()
        dependency_contributions[variable] = contribution

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

    df = calculate_dependency_contributions(sim, variable_name, year, top_n=top_n)

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
    fonts = HTML("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:ital,opsz,wght@0,8..144,100..900;1,8..144,100..900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet">
    """)
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
