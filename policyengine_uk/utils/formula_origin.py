"""Whether a simulation calculates a variable with the model's own formula."""

import os


def calculated_by(population, variable_name, period, model_variable):
    """Whether the simulation calculates ``variable_name`` with the model's own
    formula (``model_variable``'s), rather than one a reform put in its place.
    The tax-benefit system loads each variable file as its own module, so the
    formula is matched by where its code is, not by identity."""
    from policyengine_uk.scenarios.uc_reform import lcwra_formula_origin

    variable = population.simulation.tax_benefit_system.get_variable(variable_name)
    formula = lcwra_formula_origin(variable.get_formula(period), period)
    code = getattr(formula, "__code__", None)
    model = model_variable.formula.__code__
    return code is not None and (
        os.path.realpath(code.co_filename),
        code.co_firstlineno,
    ) == (os.path.realpath(model.co_filename), model.co_firstlineno)
