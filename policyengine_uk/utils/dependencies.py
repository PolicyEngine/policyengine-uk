import re
from contextlib import contextmanager

import numpy as np
from policyengine_core import periods
from policyengine_core.enums import EnumArray
from policyengine_core.variables import QuantityType
from policyengine_uk.system import system
from policyengine_uk.utils.supplied_inputs import (
    SUPPLIED_INPUT_VARIABLES,
    record_model_value,
    same_array,
    stored_as_input,
    supplied_input,
)
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

    A formula that ran shows the variables it read as the node's children and
    the parameters it read as the node's parameters. A read of a variable core
    already calculated leaves a node with neither, and so does a formula that
    read neither (see calculation_again). The index lists the nodes with
    either, in the order core calculated them. Also returns the keys of every
    node.
    """
    calculations, keys = {}, set()
    stack = list(reversed(tracer.trees))
    while stack:
        node = stack.pop()
        key = (node.name, periods.period(node.period), node.branch_name)
        keys.add(key)
        if node.children or node.parameters:
            calculations.setdefault(key, []).append(node)
        stack.extend(reversed(node.children))
    return calculations, keys


def comparable(values):
    # Enum values by name: a calculation the caller asks for directly decodes
    # them (see Simulation.calculate), and one a formula asks for does not.
    if isinstance(values, EnumArray):
        return values.decode_to_str()
    return np.asarray(values)


def same_values(a, b):
    try:
        return same_array(comparable(a), comparable(b))
    except (TypeError, ValueError):
        return False


def latest_calculation(nodes, value=None):
    # The latest calculation that gave a value, or with value the latest that
    # gave value, or None if none did. A branch keeps the values its parent
    # held when the parent created it, so the parent's latest calculation need
    # not be the one that gave the branch its value.
    for node in reversed(nodes):
        if node.value is not None and (value is None or same_values(node.value, value)):
            return node
    return None


def no_calculation_gave(variable_name, period):
    return ValueError(
        f"The simulation holds values of '{variable_name}' over {period} that "
        f"no calculation in the trace gave and its formula does not give (a "
        f"caller stored them, say), so nothing shows what they read."
    )


def calculation_again(sim, variable_name, period, value=None):
    # variable_name's calculation over period, from running it again, as if sim
    # had run it. None if it does not give value. The trace can show a read of
    # values with no calculation of them over that period:
    # - a formula that reads neither a variable nor a parameter (a constant, a
    #   variable with no formula) leaves the same node as a read of a stored
    #   value;
    # - core keeps one value of a stock under its definition period, and of an
    #   eternal variable under eternity, so the calculation that gave it can
    #   sit under any period that reads that value;
    # - calculate_add and calculate_divide store their result with no node of
    #   the variable over that period;
    # - the simulation can calculate values before tracing began.
    # Core rejects a formula whose own code references randomness when it builds
    # the variable (check_formula_determinism), though not the helpers a formula
    # calls. Equal values don't show equal reads: what the formula reads can
    # have changed since the calculation that gave them, and a formula can ask
    # what the simulation stores. This run's nodes go to a tracer of its own, on
    # a branch the function removes, so sim keeps its trace and values, apart
    # from what a formula does to its parent or another simulation. The
    # limitations of calculate_dependency_contributions cover all of these. An
    # error the formula raises on this run reaches the caller.
    with branch_without(sim, variable_name, period, trace=True) as branch:
        result = branch.calculate(variable_name, period)
        node = next(node for node in branch.tracer.trees if node.name == variable_name)
    if value is not None and not same_values(result, value):
        return None
    stack = [node]
    while stack:
        current = stack.pop()
        if current.branch_name == branch.branch_name:
            current.branch_name = sim.branch_name
        stack.extend(current.children)
    return node


def find_calculation(variable_name, period, sim, calculations, keys, value=None):
    # The node of variable_name's calculation over period: the latest on the
    # first branch of sim's chain that calculated it, or with value the latest
    # on the first branch of the chain with one that gave value (see
    # latest_calculation). Failing that, the calculation run again, if it gives
    # value (see calculation_again). None if the system neutralizes
    # variable_name: it reads as its default, whatever a calculation of equal
    # values read. An error if the trace shows it but nothing gives value, or
    # if the trace does not show it.
    period = periods.period(period)
    if sim.tax_benefit_system.variables[variable_name].is_neutralized:
        return None
    shown = False
    for branch_name in branch_chain(sim):
        key = (variable_name, period, branch_name)
        nodes = calculations.get(key)
        if nodes:
            node = latest_calculation(nodes, value)
            if node is not None:
                return node
        shown = shown or key in keys
    if not shown:
        raise ValueError(
            f"The trace shows no calculation of '{variable_name}' over {period}. "
            f"Calculate it with trace=True."
        )
    node = calculation_again(sim, variable_name, period, value)
    if node is None:
        raise no_calculation_gave(variable_name, period)
    return node


def is_period_wrapper(child, node):
    # A variable calculated over a period other than its definition period (a
    # monthly one summed over a year, or a yearly one divided into a month)
    # has itself as a child on the same branch for each period core
    # calculates it over.
    child_period = periods.period(child.period)
    node_period = periods.period(node.period)
    return (
        child.name == node.name
        and child.branch_name == node.branch_name
        and child_period != node_period
        and (node_period.contains(child_period) or child_period.contains(node_period))
    )


def calculation_read(child, sim, calculations):
    # Finds the calculation that stored the value child read (child has no
    # children and sits on a branch of sim's chain): the latest that gave
    # child's value, on child's branch or the first of its ancestors with one.
    # Failing that, runs the formula again and takes that run if it gives that
    # value (see calculation_again). Raises otherwise.
    period = periods.period(child.period)
    chain = branch_chain(sim)
    for branch_name in chain[chain.index(child.branch_name) :]:
        found = calculations.get((child.name, period, branch_name))
        if found:
            node = latest_calculation(found, child.value)
            if node is not None:
                return node
    node = calculation_again(sim, child.name, period, child.value)
    if node is None:
        raise no_calculation_gave(child.name, period)
    return node


def get_dependency_nodes(node, sim=None, calculations=None):
    # The nodes of what node read directly: what it read is under its period
    # wrappers (see is_period_wrapper). A wrapper that read a value already
    # stored has no children of its own, so calculations (from index_trace)
    # gives the calculation that stored it (see calculation_read). The
    # variable read on another branch is a dependency, and so is the variable
    # read over a period that neither contains its own nor lies within it. A
    # node with no value raised and a formula caught the error, so it gave node
    # nothing.
    nodes = []
    for child in node.children:
        if child.value is None:
            continue
        if is_period_wrapper(child, node):
            if not child.children and calculations is not None:
                child = calculation_read(child, sim, calculations)
            nodes.extend(get_dependency_nodes(child, sim, calculations))
        else:
            nodes.append(child)
    return nodes


def get_variable_dependencies(variable_name, sim, period=None):
    """The variables variable_name reads directly, from sim's trace.

    With period, those its latest calculation over period read, once each
    (get_direct_reads says which calculation, and when it raises); otherwise
    those of the first node of variable_name the trace shows.
    """
    if period is None:
        node = find_variable_in_trees(variable_name, sim.tracer)
        if not node:
            return []
        return [child.name for child in get_dependency_nodes(node)]
    reads = get_direct_reads(variable_name, sim, period)
    return list(dict.fromkeys(name for _, name in reads))


def check_not_input(variable_name, sim, period):
    # A value set as an input reads nothing, and a calculation of it that
    # the trace shows read what gave another value. A neutralized variable
    # reads as its default, whatever the simulation holds.
    variable = sim.tax_benefit_system.variables[variable_name]
    if variable.is_neutralized:
        return
    inputs = sim.get_holder(variable_name).get_input_periods(sim.branch_name)
    for held in definition_periods(variable, [period]):
        if held in inputs:
            raise ValueError(
                f"The simulation holds '{variable_name}' over {held} as an "
                f"input, which reads nothing, so no variable read contributes "
                f"to it."
            )


def get_direct_reads(variable_name, sim, period, value=None):
    """What variable_name, calculated over period, read directly.

    From sim's trace, in the calculation that gave value (see
    latest_calculation): a dict from (branch, variable) to a dict from each
    period read to the latest node of that read, in the order of the first
    read of each variable. branch is None for sim's branch and its ancestors
    (sim reads their values as its own), and otherwise the name of the
    branch read.

    Where no calculation in the trace gave value, or the values a calculation
    of variable_name read from storage, the reads come from running the
    formula again, if it gives them (see calculation_again). A neutralized
    variable reads as its default, so it reads nothing.

    Raises ValueError if sim holds variable_name as an input over one of its
    definition periods within period, which reads nothing, unless the system
    neutralizes it. Also raises if nothing gives those values.
    """
    period = periods.period(period)
    check_not_input(variable_name, sim, period)
    calculations, keys = index_trace(sim.tracer)
    chain = branch_chain(sim)
    node = find_calculation(variable_name, period, sim, calculations, keys, value)
    reads = {}
    if node is None:
        return reads
    for child in get_dependency_nodes(node, sim, calculations):
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
    # The definition periods of variable that make up each read period, or
    # that contain it (the year a month of a yearly variable falls in). A
    # stock read over a longer period than its own takes its value in the
    # last.
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


@contextmanager
def branch_without(sim, variable_name, period, trace=False):
    # A new branch of sim that holds no value of variable_name over period or
    # the definition periods that make it up or contain it, and so calculates
    # it again: a yearly variable over a month divides whatever the branch
    # holds for the year. The branch has a tax-benefit system of its own and,
    # with trace, a tracer of its own. Removes it from sim.branches on exit.
    variable = sim.tax_benefit_system.variables[variable_name]
    branch_name = unused_branch_name(sim)
    branch = sim.get_branch(branch_name, clone_system=True)
    try:
        # Setting trace gives the branch a new tracer, whichever the value.
        branch.trace = trace
        for deleted in [period, *definition_periods(variable, [period])]:
            branch.delete_arrays(variable_name, deleted)
        yield branch
    finally:
        sim.branches.pop(branch_name, None)


def overlaps(period, other):
    return period.contains(other) or other.contains(period)


def check_reads_of_itself(variable_name, period, reads):
    # Recalculating variable_name over period replaces its values there, so a
    # read of its own value within period cannot keep the value it read.
    for read_period in reads.get((None, variable_name), {}):
        if overlaps(period, read_period):
            raise ValueError(
                f"'{variable_name}' reads its own value over {read_period}, "
                f"within {period}, and recalculating it over {period} "
                f"replaces that value, so no recalculation can hold what it "
                f"read. Calculate the contributions over each of its "
                f"definition periods instead."
            )


def check_entities_read(sim, variable_name, on, name, read):
    # The recalculation holds a value read on another branch for the branch
    # of that name it makes, so the value needs one entry for each entity in
    # sim. A branch of a subset of households (utils/household_subset.py)
    # holds fewer, and the trace does not show which: the recalculation's
    # subset then holds the households its values select, which zeroing
    # can change.
    if on is None:
        return
    count = sim.get_variable_population(name).count
    for node in read.values():
        shape = np.shape(node.value) if node.value is not None else ()
        if shape and shape[0] != count:
            raise ValueError(
                f"'{variable_name}' read '{name}' on branch '{on}', which "
                f"holds {shape[0]} values of it where the simulation holds "
                f"{count}: a branch of a subset of households (see "
                f"utils/household_subset.py). The contributions cannot hold "
                f"what it read there, as the recalculation's subset need not "
                f"hold the same households."
            )


def value_held(sim, on, name, read, held):
    # The value of name over held that variable_name read on branch on (None
    # for sim's branch and its ancestors), with whether sim holds it there:
    # the one sim holds, or else the one the trace shows (or the branch of
    # sim named on holds).
    variable = sim.tax_benefit_system.variables[name]
    if on is None:
        value = sim.get_holder(name).get_array(held, sim.branch_name)
        if value is not None:
            return value, True
    value = value_read(variable, read, held)
    if value is None and on in sim.branches:
        value = sim.branches[on].get_holder(name).get_array(held, on)
    return value, False


def how_held(sim, on, name, period, value):
    # How the simulation held value, the value of name over period read on
    # branch on (None for sim's branch and its ancestors), as the helpers in
    # utils/supplied_inputs.py tell it: "supplied", "model" (the model's own,
    # set_model_value) or "calculated". None for a variable those helpers do
    # not answer for. A branch the recalculation makes in place of one sim
    # no longer holds (a formula drops its branches) holds sim's value, and
    # value is sim's if it is the one sim holds. A value sim does not hold
    # counts as calculated.
    if name not in SUPPLIED_INPUT_VARIABLES:
        return None
    source = sim.branches.get(on, sim) if on is not None else sim
    holds = source.get_holder(name).get_array(period, source.branch_name)
    if holds is None or not same_values(holds, value):
        return "calculated"
    population = source.get_variable_population(name)
    if supplied_input(population, name, period) is not None:
        return "supplied"
    if stored_as_input(population, name, period):
        return "model"
    return "calculated"


def calculate_with_dependency_zeroed(
    sim, variable_name, dependency, year, map_to=None, reads=None
):
    """Recalculate variable_name over year with dependency zero.

    reads (by default get_direct_reads(variable_name, sim, year)) gives what
    variable_name read directly, the periods it read each variable over, and
    the branch it read it on. Wherever variable_name read dependency, the
    function sets it to zero for each of its definition periods that make up
    or contain a period read. Every other variable read keeps the value it
    had, apart from the limitations calculate_dependency_contributions lists,
    so the difference from variable_name's value is the change from
    dependency alone. The function returns the recalculated values, not that
    difference.

    Runs on a new untraced branch of sim, which it removes from sim.branches
    before returning: what the branch stores or deletes stays in the branch,
    so sim stays as it was. The branch has a tax-benefit system of its own, so a
    formula that takes values from the nearest ancestor with the same system
    (response_source in utils/labour_supply_responses.py) takes them from the
    branch, not from sim.

    The function stores the zeros, and a value read the branch does not hold,
    as inputs straight into the branch's holders. Simulation.set_input would
    also drop the values calculated from the value it replaces, and the branch
    would then work those out again with dependency zero. As inputs, they stay
    in a branch a formula creates from it and then sets an input on. The branch
    stores a read on another branch under that branch's name, so the branch
    of that name the formula of variable_name creates from the new branch
    reads it: the value variable_name read there, from the trace (or from
    the branch of sim with that name).

    A formula that asks supplied_input or stored_as_input
    (utils/supplied_inputs.py) about a value it reads gets the answer it got
    in sim: the function records each value it stores that sim calculated,
    the zeros included, as a model value that stands for a calculation, and
    each value the model set (set_model_value) as a model value.

    Raises ValueError, before making the branch, if variable_name read on a
    branch of a subset of households (utils/household_subset.py): the
    recalculation cannot hold what it read there.
    """
    period = periods.period(year)
    if reads is None:
        reads = get_direct_reads(variable_name, sim, period)
    check_reads_of_itself(variable_name, period, reads)

    variables = sim.tax_benefit_system.variables
    deletions, inputs = [], []
    for (on, name), read in reads.items():
        check_entities_read(sim, variable_name, on, name, read)
        read_periods = list(read)
        covering = definition_periods(variables[name], read_periods)
        if name == dependency:
            zeros = np.zeros(sim.get_variable_population(name).count)
            deletions.extend((name, on, deleted) for deleted in read_periods + covering)
            for held in covering:
                value, _ = value_held(sim, on, name, read, held)
                status = how_held(sim, on, name, held, value)
                inputs.append((name, held, zeros, on, status))
            continue
        for held in covering:
            value, sim_holds = value_held(sim, on, name, read, held)
            if sim_holds:
                # The new branch reads sim's value as its own.
                continue
            if value is None:
                raise ValueError(
                    f"'{name}' over {held} cannot keep the value "
                    f"'{variable_name}' read: neither the simulation nor "
                    f"its trace holds it."
                )
            inputs.append((name, held, value, on, how_held(sim, on, name, held, value)))

    with branch_without(sim, variable_name, period) as branch:
        for name, on, deleted in deletions:
            if on is None:
                branch.delete_arrays(name, deleted)
            else:
                branch.get_holder(name).delete_arrays(deleted, on)
        for name, held, value, on, status in inputs:
            stored_under = branch.branch_name if on is None else on
            branch.get_holder(name)._set(held, value, stored_under, is_input=True)
            if status in ("model", "calculated"):
                record_model_value(
                    branch,
                    name,
                    held,
                    stored_under,
                    calculated=status == "calculated",
                )
        try:
            return branch.calculate(variable_name, period, map_to=map_to)
        except ValueError as error:
            raise ValueError(
                f"Recalculating '{variable_name}' over {period} with "
                f"'{dependency}' zero and every other variable it read held "
                f"raised: {error}"
            ) from error


def calculate_dependency_contributions(
    sim, variable_name, year, top_n=None, filter=None, map_to=None
):
    """Mean change in variable_name from zeroing each variable it reads directly.

    The variables variable_name reads directly in its calculation over year
    that gave the values sim holds, the periods it reads them over and the
    branches it reads them on, come from sim's trace, so sim needs
    trace=True. For each float one, the function recalculates variable_name
    with that variable zero wherever it read it and every other variable read
    held (see calculate_with_dependency_zeroed). Its contribution is the mean
    of variable_name minus that recalculation, after mapping to map_to and
    selecting filter if given. The function skips a variable whose name
    contains weight. So where a target only adds and subtracts float variables
    it reads, the trace shows those reads and the target's values stay finite,
    the contributions sum to its mean, unless the function skips one or top_n
    drops some. Other variables contribute zero where the target's values stay
    finite, and a calculation that read no variables, or a neutralized
    variable, has no contributions. Apart from what its own
    calculation of variable_name over year stores or drops in sim, as any
    Simulation.calculate does, sim's values stay as they were. The tax-benefit
    system needs parameters, as every PE-UK system has: the recalculation runs
    on a branch with a clone of it.

    Where no calculation in the trace gave the values sim holds (a stock over
    a period of another unit, or values calculated before tracing began, say),
    the function runs the formula again and takes what it read there, if it
    gives those values (see calculation_again). An error from that run reaches
    the caller.

    Raises ValueError if sim holds variable_name over year as an input
    (which reads nothing) and the system does not neutralize it, or if neither
    the trace nor the formula gives the values sim holds. Where a float
    dependency needs a recalculation, also raises if variable_name reads its
    own value within year, or reads on a branch of a subset of households (see
    calculate_with_dependency_zeroed).

    Limitations:

    - What a formula reads from another simulation (sim.baseline, say)
      isn't in sim's trace, so it gets no contribution and the function
      doesn't hold it. The recalculation reads it from that simulation
      afresh, from the values the formula gives it there
      (relative_income_change sets the earnings it read as inputs on a
      branch of sim.baseline), and that simulation can calculate and trace
      more.
    - A formula that names the branch it makes by the first name free on the
      simulation it runs on (marginal_tax_rate, say) takes the name it took
      in sim only if that name is free on the recalculation's branch too,
      which holds no branches. Where sim held a branch by that name, the
      formula took another in sim, the recalculation does not hold what the
      formula read on it, and the contributions change. A formula that names
      its own branch dependency-contribution, as the function names its
      branch, can show reads there as reads on sim's own branch, or raise
      core's CycleError if it calculates itself there. No PE-UK formula does.
    - Of the calculations that gave the values sim holds, the latest gives
      the reads. Where calculations with other reads gave equal values,
      that need not be the calculation the values came from: a branch keeps
      the values its parent held when the parent made it, and the parent
      can calculate equal values from other reads later. A reform can also
      replace a formula with a constant equal to what it gave, which leaves
      no calculation in the index. Where the function runs a formula again,
      equal values don't show equal reads either: what the formula reads can
      have changed since the calculation that gave them.
    - The function runs formulas again, on branches of its own. A formula that
      writes to its parent simulation (sim, on those branches) or to an object
      outside the simulation writes there again, so sim can change. PE-UK's
      formulas write to branches they make, not to their parents. What one
      writes to another simulation falls under the first limitation.
    - A formula can refuse the values the recalculation gives it, and the
      function then raises a ValueError with that formula's message and the
      dependency it zeroed, with sim as it was. The recalculation holds every
      other variable read, so state_pension_age, which reads age and
      date_of_birth, gets an age of zero with the date of birth the real age
      gave, and birth_instant (utils/dates.py) rejects them. LHA_category has
      no category for no bedrooms.
    - A formula can read a stored value with no calculation, through
      supplied_input or a holder, and the trace shows no such read. That value
      gets no contribution, and the function doesn't hold it. net_income adds
      a supplied adjusted_net_income to Gift Aid and pension relief, so with
      one supplied it shows only those two reads, and the contributions don't
      sum to it.
    - A formula that asks what the simulation stores can take another route
      when it runs again. uses_property_allowance compares income tax before
      the winter fuel payment charge until the simulation holds income_tax, so
      running it again reads income_tax where the calculation read the tax
      before the charge.
    - A target with an infinite or NaN value can have contributions that
      aren't finite: subtracting infinity from itself gives NaN, also for a
      variable that otherwise contributes zero. uc_benefit_cap holds infinity
      for an exempt household. Zeroing a variable a formula divides by can
      give infinity or NaN too (equiv_household_net_income divides by
      household_equivalisation_bhc).
    - The function subtracts a target's values for each variable it doesn't
      skip, so a bool or enum target raises TypeError there, unless an error
      above comes first.
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
