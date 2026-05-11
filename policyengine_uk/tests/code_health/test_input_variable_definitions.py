from policyengine_uk import CountryTaxBenefitSystem


def test_input_variables_do_not_use_defined_for():
    system = CountryTaxBenefitSystem()

    invalid = {
        name: variable.defined_for
        for name, variable in system.variables.items()
        if variable.is_input_variable() and variable.defined_for is not None
    }

    assert invalid == {}


def test_input_variables_do_not_use_formulas_adds_or_subtracts():
    system = CountryTaxBenefitSystem()

    invalid = {
        name: {
            "formulas": bool(getattr(variable, "formulas", None)),
            "adds": bool(getattr(variable, "adds", None)),
            "subtracts": bool(getattr(variable, "subtracts", None)),
        }
        for name, variable in system.variables.items()
        if variable.is_input_variable()
        and (
            getattr(variable, "formulas", None)
            or getattr(variable, "adds", None)
            or getattr(variable, "subtracts", None)
        )
    }

    assert invalid == {}
