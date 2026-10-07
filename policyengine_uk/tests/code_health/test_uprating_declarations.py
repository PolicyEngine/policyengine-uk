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

UPRATING_INDICES = Path(__file__).parents[2] / "data" / "uprating_indices.yaml"

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
    # policyengine-uk-data stores energy spend already priced at the dataset's
    # target price level (Ofgem Q2 2026 unit rates), so CPI-uprating from the
    # data year re-applies price changes the build has priced in (#1868).
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
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


def _uprated_by_another_index(declared, listed_index):
    # The YAML keys are yoy_growth twins of the declared indices.
    equivalent = declared.replace(".indices.", ".yoy_growth.")
    return listed_index not in (declared, equivalent)


def test_the_yaml_uprates_by_the_declared_index():
    listed = _listed_indices()
    mismatched = []
    for name, variable in CountryTaxBenefitSystem().variables.items():
        declared = getattr(variable, "uprating", None)
        if not declared or name not in listed or name in KNOWN_INDEX_OVERRIDES:
            continue
        if _uprated_by_another_index(declared, listed[name]):
            mismatched.append((name, declared, listed[name]))
    assert not mismatched, (
        "these variables are uprated by a different index from the one they "
        f"declare: {mismatched}"
    )


def _stale_exceptions(variables, listed, unuprated, index_overrides):
    """Return a message for every exception whose reason no longer holds."""
    stale = []
    for name in sorted(unuprated | index_overrides):
        if name not in variables:
            stale.append(f"{name} no longer exists; drop the exception")
        elif not getattr(variables[name], "uprating", None):
            stale.append(f"{name} no longer declares uprating; drop the exception")
    for name in sorted(unuprated & variables.keys()):
        if name in listed:
            stale.append(
                f"{name} is now in uprating_indices.yaml under {listed[name]}; "
                "remove it from KNOWN_UNUPRATED"
            )
    for name in sorted(index_overrides & variables.keys()):
        declared = getattr(variables[name], "uprating", None)
        if not declared:
            continue
        if name not in listed:
            stale.append(
                f"{name} is no longer in uprating_indices.yaml, so there is no "
                "index to override; remove it from KNOWN_INDEX_OVERRIDES"
            )
        elif not _uprated_by_another_index(declared, listed[name]):
            stale.append(
                f"{name} is now uprated by its declared index ({declared}); "
                "remove it from KNOWN_INDEX_OVERRIDES"
            )
    return stale


def test_every_known_exception_still_holds():
    """Keeps the exception lists honest: an entry whose reason no longer
    holds should be removed rather than left to hide a future gap."""
    stale = _stale_exceptions(
        CountryTaxBenefitSystem().variables,
        _listed_indices(),
        KNOWN_UNUPRATED,
        KNOWN_INDEX_OVERRIDES,
    )
    assert not stale, "stale uprating exceptions:\n" + "\n".join(stale)


class _Declares:
    def __init__(self, uprating=None):
        self.uprating = uprating


CPI = "gov.economic_assumptions.indices.obr.consumer_price_index"
CPI_YOY = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"
GDP_YOY = "gov.economic_assumptions.yoy_growth.obr.per_capita.gdp"


def test_the_guard_passes_exceptions_that_still_hold():
    variables = {"a": _Declares(CPI), "b": _Declares(CPI)}
    listed = {"b": GDP_YOY}
    assert _stale_exceptions(variables, listed, {"a"}, {"b"}) == []


def test_the_guard_flags_an_unuprated_exception_added_to_the_yaml():
    variables = {"a": _Declares(CPI)}
    (stale,) = _stale_exceptions(variables, {"a": CPI_YOY}, {"a"}, set())
    assert "remove it from KNOWN_UNUPRATED" in stale


def test_the_guard_flags_an_override_that_now_matches():
    variables = {"b": _Declares(CPI)}
    (stale,) = _stale_exceptions(variables, {"b": CPI_YOY}, set(), {"b"})
    assert "remove it from KNOWN_INDEX_OVERRIDES" in stale


def test_the_guard_flags_an_override_dropped_from_the_yaml():
    variables = {"b": _Declares(CPI)}
    (stale,) = _stale_exceptions(variables, {}, set(), {"b"})
    assert "remove it from KNOWN_INDEX_OVERRIDES" in stale


def test_the_guard_flags_missing_or_undeclared_exceptions():
    variables = {"a": _Declares(None)}
    stale = _stale_exceptions(variables, {}, {"a", "gone"}, set())
    assert stale == [
        "a no longer declares uprating; drop the exception",
        "gone no longer exists; drop the exception",
    ]
