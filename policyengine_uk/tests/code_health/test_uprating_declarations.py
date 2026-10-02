"""Every variable declaring `uprating` should appear in uprating_indices.yaml.

The class-level `uprating = "..."` attribute on a Variable is dead metadata:
nothing in policyengine-uk reads it, and policyengine-core only inspects it to
refuse combining it with its own `@uprated` decorator. `uprating_indices.yaml`
is the only mechanism that applies uprating, via `apply_single_year_uprating`
and `reset_growthfactor_uprating` in `data/economic_assumptions.py`.

A variable can therefore declare an index and silently never be uprated. That
is what #1859 found for electricity and gas consumption, and #1862 for three
more columns. This guard makes the gap fail loudly at the point it is
introduced rather than surfacing in a downstream study.
"""

from pathlib import Path

import yaml

from policyengine_uk import CountryTaxBenefitSystem

UPRATING_INDICES = (
    Path(__file__).parents[2] / "data" / "uprating_indices.yaml"
)

# Variables that declare an index but are deliberately not in the YAML, with
# the reason. Anything else failing this test is a genuine gap.
KNOWN_UNUPRATED = {
    # gov.dft.rail.ridership_index is a CUMULATIVE index (2020 = 1.0), not a
    # year-on-year growth rate, so it cannot go in a yoy_growth list without
    # compounding wrongly: doing so uprates rail_usage by ~684% over 2024-27.
    # Uprating this needs a yoy series, not a YAML entry (#1862).
    "rail_usage",
    # Reported counterpart of employee_pension_contributions, which IS
    # uprated; the reported variable feeds imputation rather than results.
    "employee_pension_contributions_reported",
}

# Variables the YAML deliberately uprates by an index other than the one they
# declare, with the reason.
KNOWN_INDEX_OVERRIDES = {
    # Declares ons.household_interest_income; the YAML applies per_capita.gdp.
    # Flagged in #1862 for someone with the context to say which is intended.
    "savings_interest_income",
}


def _listed_indices():
    listed = yaml.safe_load(UPRATING_INDICES.read_text())
    return {
        variable: index for index, variables in listed.items() for variable in variables
    }


def test_declared_uprating_variables_are_in_the_yaml():
    listed = _listed_indices()
    missing = sorted(
        name
        for name, variable in CountryTaxBenefitSystem().variables.items()
        if getattr(variable, "uprating", None)
        and name not in listed
        and name not in KNOWN_UNUPRATED
    )
    assert not missing, (
        "these variables declare `uprating` but are absent from "
        f"uprating_indices.yaml, so they are never uprated: {missing}. Add "
        "them to the matching index block, or to KNOWN_UNUPRATED with a reason."
    )


def test_the_yaml_uprates_by_the_declared_index():
    listed = _listed_indices()
    mismatched = []
    for name, variable in CountryTaxBenefitSystem().variables.items():
        declared = getattr(variable, "uprating", None)
        if not declared or name not in listed or name in KNOWN_INDEX_OVERRIDES:
            continue
        # The YAML keys are yoy_growth twins of the declared indices.
        equivalent = declared.replace(".indices.", ".yoy_growth.")
        if listed[name] not in (declared, equivalent):
            mismatched.append((name, declared, listed[name]))
    assert not mismatched, (
        "these variables are uprated by a different index from the one they "
        f"declare: {mismatched}"
    )


def test_every_known_exception_still_declares_uprating():
    """Keeps the exception lists honest: an entry that no longer declares
    uprating, or no longer exists, should be removed rather than left."""
    variables = CountryTaxBenefitSystem().variables
    for name in KNOWN_UNUPRATED | KNOWN_INDEX_OVERRIDES:
        assert name in variables, f"{name} no longer exists; drop the exception"
        assert getattr(variables[name], "uprating", None), (
            f"{name} no longer declares uprating; drop the exception"
        )
