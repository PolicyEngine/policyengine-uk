from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *
import inspect
import re


class VariableGraph:
    def __init__(self, tax_benefit_system, period="2020-06-01"):
        self.nodes = {}
        variables = tax_benefit_system.variables
        formulas = {
            var: variables[var].get_formula(period) for var in variables
        }
        formula_text = {}
        for var in variables:
            if formulas[var]:
                formula_text[var] = inspect.getsource(formulas[var]).replace(
                    "'", '"'
                )
            else:
                formula_text[var] = ""
        immediate_children = {
            var: _get_dependencies_in_formula(formula_text[var])
            for var in variables
        }
        for var in variables:
            self.add(var)
        for var in variables:
            for dependency in immediate_children[var]:
                if dependency in variables:
                    self.add_dependency(var, dependency)

    def get_dependencies(self, name):
        node = self.nodes[name]
        direct_dependencies = node.dependencies
        flatten = lambda t: [item for sublist in t for item in sublist]
        if len(direct_dependencies) > 0:
            indirect_dependencies = flatten(
                [self.get_dependents(n) for n in direct_dependencies]
            )
        else:
            indirect_dependencies = []
        return list(set(direct_dependencies + indirect_dependencies))

    def get_dependents(self, name):
        node = self.nodes[name]
        direct_dependents = node.dependents
        flatten = lambda t: [item for sublist in t for item in sublist]
        if len(direct_dependents) > 0:
            indirect_dependents = flatten(
                [self.get_dependents(n) for n in direct_dependents]
            )
        else:
            indirect_dependents = []
        return list(set(direct_dependents + indirect_dependents))

    def add_dependency(self, x, y):
        self.nodes[x].dependencies += [y]
        self.nodes[y].dependents += [x]

    def add(self, name):
        self.nodes[name] = VariableNode(name)


class VariableNode:
    def __init__(self, name):
        self.name = name
        self.dependencies = []
        self.dependents = []


def _get_dependencies_in_formula(formula_text):
    FORMULA = '(?:"(\w+)")'
    matches = re.findall(FORMULA, formula_text)
    return matches
