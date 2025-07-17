import inspect
import re
from policyengine_uk.system import system

def get_variable_dependencies(variable_name):
    # First, check for adds/subtracts
    variable = system.get_variable(variable_name)
    deps = []
    if variable.adds:
        deps.extend(variable.adds)
    if variable.subtracts:
        deps.extend(variable.subtracts)
    # Then, check for formula


    formula = variable.get_formula(2025)
    if formula is not None:
        formula_source = inspect.getsource(formula)
        deps.extend(extract_variables_regex(formula_source))
    
    return deps

def extract_variables_regex(formula_source):
    # Find all strings in double quotes that look like variable names
    pattern = r'benunit\(\s*["\']([^"\']+)["\']\s*,'
    matches = re.findall(pattern, formula_source)
    return matches

def calculate_dependency_contributions(sim, variable_name, year):
    original_values = sim.calculate(variable_name, year)
    dependency_contributions = {}
    for variable in get_variable_dependencies(variable_name):
        sim.get_holder(variable_name).delete_arrays(year)
        value_type = system.get_variable(variable).value_type
        current_values = sim.calculate(variable, year)
        if value_type == bool:
            sim.set_input(variable, year, (current_values * 0).astype(bool))
        elif value_type == float:
            sim.set_input(variable, year, (current_values * 0).astype(float))
        
        new_values = sim.calculate(variable_name, year)
        contribution = original_values.sum() - new_values.sum()
        dependency_contributions[variable] = contribution
        sim.set_input(variable_name, year, original_values)
        sim.set_input(variable, year, current_values)
    
    return dependency_contributions
