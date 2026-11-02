import re
import numpy as np
from policyengine_core import periods
from policyengine_core.variables import QuantityType
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


def branch_chain(sim):
    # The branch names sim reads values under: its own, then each ancestor's.
    names = []
    ancestor = sim
    while ancestor is not None:
        names.append(ancestor.branch_name)
        ancestor = getattr(ancestor, "parent_branch", None)
    return names


def index_trace(tracer):
    """Index the trace's calculations by (variable, period, branch name).

    A variable read again after it was calculated gets a node without
    children, so a calculation's node is one with children: the index lists
    them in the order calculated. Also returns the keys of every node, with
    children or not.
    """
    calculations, keys = {}, set()
    stack = list(reversed(tracer.trees))
    while stack:
        node = stack.pop()
        key = (node.name, periods.period(node.period), node.branch_name)
        keys.add(key)
        if node.children:
            calculations.setdefault(key, []).append(node)
            stack.extend(reversed(node.children))
    return calculations, keys


def same_values(a, b):
    try:
        return np.array_equal(np.asarray(a), np.asarray(b))
    except (TypeError, ValueError):
        return False


def latest_calculation(nodes, value=None):
    # The latest calculation that gave value, or the latest if none did or
    # value is None. A branch keeps the values its parent held when the
    # branch was created, so the parent's latest calculation need not be the
    # one that gave the branch its value.
    if value is not None:
        for node in reversed(nodes):
            if node.value is not None and same_values(node.value, value):
                return node
    return nodes[-1]


def branches_read_from(branch_name, chain):
    # A value read on a branch of chain may have been calculated on any
    # branch after it in chain (an ancestor's); one read on another branch,
    # on that branch.
    if branch_name in chain:
        return chain[chain.index(branch_name) :]
    return [branch_name]


def find_calculation(variable_name, period, chain, calculations, keys, value=None):
    # The node of variable_name's calculation over period that gave value (see
    # latest_calculation), on the first branch of chain that calculated it,
    # or None if the trace shows variable_name over period with no variables
    # read (a formula of parameters alone, say).
    period = periods.period(period)
    for branch_name in chain:
        nodes = calculations.get((variable_name, period, branch_name))
        if nodes:
            return latest_calculation(nodes, value)
    if any((variable_name, period, branch_name) in keys for branch_name in chain):
        return None
    raise ValueError(
        f"The trace shows no calculation of '{variable_name}' over {period}. "
        f"Calculate it with trace=True."
    )


def is_period_wrapper(child, node):
    # A variable calculated over a period other than its definition period (a
    # monthly one summed over a year, or a yearly one divided into a month)
    # has itself as a child on the same branch for each period it is
    # calculated over.
    child_period = periods.period(child.period)
    node_period = periods.period(node.period)
    return (
        child.name == node.name
        and child.branch_name == node.branch_name
        and child_period != node_period
        and (node_period.contains(child_period) or child_period.contains(node_period))
    )


def get_dependency_nodes(node, calculations=None, chain=None):
    # The nodes of what node read directly: what it read is under its period
    # wrappers (see is_period_wrapper). A wrapper that read a value already
    # stored has no children of its own, so calculations (from index_trace)
    # gives the calculation that stored it. The variable read on another
    # branch is a dependency, as is the variable read over a period that
    # neither contains nor is contained in its own.
    nodes = []
    for child in node.children:
        if is_period_wrapper(child, node):
            if not child.children and calculations is not None:
                child_period = periods.period(child.period)
                for branch_name in branches_read_from(child.branch_name, chain or []):
                    found = calculations.get((child.name, child_period, branch_name))
                    if found:
                        child = latest_calculation(found, child.value)
                        break
            nodes.extend(get_dependency_nodes(child, calculations, chain))
        else:
            nodes.append(child)
    return nodes


def get_variable_dependencies(variable_name, sim, period=None):
    """The variables variable_name reads directly, from sim's trace.

    With period, those its latest calculation over period read; otherwise
    those of the first node of variable_name the trace shows.
    """
    if period is None:
        node = find_variable_in_trees(variable_name, sim.tracer)
        if not node:
            return []
        return [child.name for child in get_dependency_nodes(node)]
    calculations, keys = index_trace(sim.tracer)
    chain = branch_chain(sim)
    node = find_calculation(variable_name, period, chain, calculations, keys)
    if node is None:
        return []
    return [child.name for child in get_dependency_nodes(node, calculations, chain)]


def get_direct_reads(variable_name, sim, period, value=None):
    """What variable_name, calculated over period, read directly.

    From sim's trace, in the calculation that gave value if one did (see
    latest_calculation): a dict from (branch, variable) to a dict from each
    period read to the latest node of that read, in the order of the first
    read of each variable. branch is None for sim's branch and its ancestors
    (sim reads their values as its own), and otherwise the name of the
    branch read.
    """
    calculations, keys = index_trace(sim.tracer)
    chain = branch_chain(sim)
    node = find_calculation(variable_name, period, chain, calculations, keys, value)
    reads = {}
    if node is None:
        return reads
    for child in get_dependency_nodes(node, calculations, chain):
        on = None if child.branch_name in chain else child.branch_name
        reads.setdefault((on, child.name), {})[periods.period(child.period)] = child
    return reads


def value_read(variable, read, period):
    # The value the nodes of read (from get_direct_reads) show variable had
    # over period: a node's own, or that of a period wrapper under it. A stock
    # read over a period whose value is its value over period (see
    # definition_periods) has no node over period.
    for node in read.values():
        stack = [node]
        while stack:
            current = stack.pop()
            if periods.period(current.period) == period:
                if current.value is not None:
                    return current.value
                continue
            stack.extend(
                child for child in current.children if is_period_wrapper(child, current)
            )
    if variable.quantity_type == QuantityType.STOCK:
        for read_period, node in read.items():
            if node.value is not None and definition_periods(
                variable, [read_period]
            ) == [period]:
                return node.value
    return None


def definition_periods(variable, read_periods):
    # The periods variable is defined for that make up each read period, or
    # that contain it (the year a month of a yearly variable is in). A stock
    # read over a longer period than its own is its value in the last.
    unit = variable.definition_period
    result = []
    for read_period in read_periods:
        if unit == periods.ETERNITY:
            covering = [periods.period(periods.ETERNITY)]
        elif unit == read_period.unit:
            # Starting where read_period starts: a year can start in any
            # month (year:2026-07).
            first = read_period.start.period(unit)
            covering = [first.offset(i, unit) for i in range(read_period.size)]
        elif periods.unit_weight(unit) < periods.unit_weight(read_period.unit):
            covering = read_period.get_subperiods(unit)
            if variable.quantity_type == QuantityType.STOCK:
                covering = covering[-1:]
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
    taken = set(sim.branches) | set(branch_chain(sim))
    name, suffix = base_name, 1
    while name in taken:
        suffix += 1
        name = f"{base_name}-{suffix}"
    return name


def overlaps(period, other):
    return period.contains(other) or other.contains(period)


def check_reads_of_itself(variable_name, period, reads):
    # Recalculating variable_name over period replaces its values there, so a
    # read of its own value within period cannot keep the value it read.
    for read_period in reads.get((None, variable_name), {}):
        if overlaps(period, read_period):
            raise ValueError(
                f"'{variable_name}' reads its own value over {read_period}, "
                f"within {period}, so its direct dependencies over {period} "
                f"cannot be zeroed one at a time. Calculate the contributions "
                f"over each period it is defined for instead."
            )


def calculate_with_dependency_zeroed(
    sim, variable_name, dependency, year, map_to=None, reads=None
):
    """Recalculate variable_name over year with dependency zero.

    reads (by default get_direct_reads(variable_name, sim, year)) gives what
    variable_name read directly, the periods it read each variable over, and
    the branch it read it on. Wherever variable_name read dependency, its
    value is zero for each period it is defined for that makes up or
    contains a period read. Every other variable read keeps the value it
    had, so the result is the change from dependency alone.

    Runs on a new untraced branch of sim, removed from sim.branches before
    returning: what the branch stores or deletes stays in the branch, so sim
    is left as it was. The branch has a tax-benefit system of its own, so a
    formula that takes values from the nearest ancestor with the same system
    (response_source in utils/labour_supply_responses.py) takes them from the
    branch, not from sim.

    The branch stores the zeros, and a value read that it does not hold, as
    inputs straight into its holders: Simulation.set_input would also drop
    the values calculated from the value it replaces, and the recalculation
    would recalculate those with dependency zero. As inputs, they stay in a
    branch a formula creates from it and then sets an input on. A read on
    another branch is stored under that branch's name, so the branch of that
    name the formula of variable_name creates from the new branch reads it:
    the value variable_name read there, from the trace (or from the branch of
    sim with that name).
    """
    period = periods.period(year)
    variables = sim.tax_benefit_system.variables
    if reads is None:
        reads = get_direct_reads(variable_name, sim, period)
    check_reads_of_itself(variable_name, period, reads)

    branch_name = unused_branch_name(sim)
    branch = sim.get_branch(branch_name, clone_system=True)
    try:
        branch.trace = False
        deletions, inputs = [], []
        for (on, name), read in reads.items():
            stored_under = branch.branch_name if on is None else on
            read_periods = list(read)
            covering = definition_periods(variables[name], read_periods)
            if name == dependency:
                zeros = np.zeros(sim.get_variable_population(name).count)
                deletions.extend(
                    (name, on, deleted) for deleted in read_periods + covering
                )
                inputs.extend((name, held, zeros, stored_under) for held in covering)
                continue
            for held in covering:
                if on is None:
                    if (
                        branch.get_holder(name).get_array(held, stored_under)
                        is not None
                    ):
                        continue
                    value = value_read(variables[name], read, held)
                else:
                    value = value_read(variables[name], read, held)
                    if value is None and on in sim.branches:
                        value = sim.branches[on].get_holder(name).get_array(held, on)
                if value is None:
                    raise ValueError(
                        f"'{name}' over {held} cannot keep the value "
                        f"'{variable_name}' read: neither the simulation nor "
                        f"its trace holds it."
                    )
                inputs.append((name, held, value, stored_under))

        branch.delete_arrays(variable_name, period)
        for name, on, deleted in deletions:
            if on is None:
                branch.delete_arrays(name, deleted)
            else:
                branch.get_holder(name).delete_arrays(deleted, on)
        for name, held, value, stored_under in inputs:
            branch.get_holder(name)._set(held, value, stored_under, is_input=True)
        return branch.calculate(variable_name, period, map_to=map_to)
    finally:
        sim.branches.pop(branch_name, None)


def calculate_dependency_contributions(
    sim, variable_name, year, top_n=None, filter=None, map_to=None
):
    """Mean change in variable_name from zeroing each variable it reads directly.

    The variables variable_name reads directly in its calculation over year
    that gave the values sim holds, the periods it reads them over and the
    branches it reads them on, come from sim's trace, so sim needs
    trace=True. A float one's contribution is the mean of variable_name minus
    variable_name recalculated with that variable zero wherever it was read,
    and every other variable read held (see calculate_with_dependency_zeroed),
    after mapping to map_to and selecting filter if given. So for a target
    that adds and subtracts what it reads, the contributions sum to its mean.
    Other variables contribute zero. sim's values are left unchanged. The
    tax-benefit system needs parameters, as every PE-UK system has: the
    recalculation runs on a branch with a clone of it.
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
    reads = get_direct_reads(variable_name, sim, year, value=original_values)
    for variable in dict.fromkeys(name for _, name in reads):
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
