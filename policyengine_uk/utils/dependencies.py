import inspect
import re
from policyengine_uk.system import system
import plotly.express as px
import pandas as pd
from plotly import graph_objects as go

def find_variable_in_tree(variable_name, node):
    if node.name == variable_name:
        return node
    for child in node.children:
        result = find_variable_in_tree(variable_name, child)
        if result:
            return result
    
    raise ValueError(f"Variable '{variable_name}' not found in the simulation tree. The *first thing* you asked the simulation to calculate needs to include your target variable in its computation tree.")

def get_variable_dependencies(variable_name, sim):
    node = find_variable_in_tree(variable_name, sim.tracer.trees[0])
    if not node:
        return []
    return [child.name for child in node.children]

def extract_variables_regex(formula_source):
    # Find all strings in double quotes that look like variable names
    pattern = r'benunit\(\s*["\']([^"\']+)["\']\s*,'
    matches = re.findall(pattern, formula_source)
    return matches

def calculate_dependency_contributions(sim, variable_name, year):
    original_values = sim.calculate(variable_name, year)
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
        
        new_values = sim.calculate(variable_name, year)
        contribution = original_values.sum() - new_values.sum()
        dependency_contributions[variable] = contribution
        sim.set_input(variable_name, year, original_values)
        sim.set_input(variable, year, current_values)
    
    return pd.Series(dependency_contributions)



def calculate_dependency_contribution_change(baseline_sim, reform_sim, variable_name, year, top_n = 5):
    baseline_dependency = calculate_dependency_contributions(baseline_sim, variable_name, year)
    reform_dependency = calculate_dependency_contributions(reform_sim, variable_name, year)

    df = pd.DataFrame({
        'baseline': pd.Series(baseline_dependency),
        'reform': pd.Series(reform_dependency)
    }).fillna(0)

    df['change'] = df['reform'] - df['baseline']
    df['relative_change'] = df['change'] / df['baseline'].abs().replace(0, 1)

    # Keep the top N variables by absolute change
    if top_n is not None:
        df = df.reindex(df['change'].abs().nlargest(top_n).index)

    return df.sort_values(by='change', ascending=False)

def create_waterfall_chart(sim, variable_name, year, top_n=5):
    if not sim.trace:
        raise ValueError("Simulation must have trace enabled to create a waterfall chart.")

    df = calculate_dependency_contributions(sim, variable_name, year)

    # make a waterfall chart

    fig = go.Figure(go.Waterfall(
        name="Waterfall",
        orientation="v",
        measure=["relative"] * len(df),
        x=df.index,
        y=df.values,
        connector={"line": {"color": "rgb(63, 63, 63)", "width": 2}},
        increasing={"marker": {"color": "green"}},
        decreasing={"marker": {"color": "red"}},
        totals={"marker": {"color": "blue"}}
    ))
    return fig

def create_waterfall_change_chart(sim_1, sim_2, variable_name, year, top_n=5):
    df = calculate_dependency_contribution_change(
        sim_1, sim_2, variable_name, year, top_n=top_n
    )

    # make a waterfall chart

    fig = go.Figure(go.Waterfall(
        name="Waterfall",
        orientation="v",
        measure=["relative"] * len(df),
        x=df.index,
        y=df.change,
        connector={"line": {"color": "rgb(63, 63, 63)", "width": 2}},
        increasing={"marker": {"color": "green"}},
        decreasing={"marker": {"color": "red"}},
        totals={"marker": {"color": "blue"}}
    ))
    return fig