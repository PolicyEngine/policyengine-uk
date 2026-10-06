"""Fiscal-year conversion covers every year, however far a parameter's data runs.

Conversion used to write every year from 2015 to a fixed 2040 and leave later
years on calendar values. It now rewrites only the years whose fiscal-year
value differs from what the calendar year already holds, with no last year.

Invariants:

1. Fiscal year: from 2015 on, a year holds the parameter's value on 30 April
   of that year, or for a ``fiscal_year_blend`` parameter its day-weighted
   average over 6 April to 5 April, on every date in the year. There is no
   last year.
2. Equivalence: the result equals, on every date, writing every year from
   2015 to past the parameter's last dated value, the way conversion used to.
3. Economy: a parameter with nothing dated after 1 January in any year keeps
   the values it had.
4. Flag: every converted parameter is marked modified, as writing each year
   used to mark it.
"""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter, ParameterNode

import policyengine_uk.tax_benefit_system as tax_benefit_system
from policyengine_uk.utils.parameters import (
    FIRST_FISCAL_YEAR,
    convert_to_fiscal_year_parameters,
    fiscal_year_average,
)


def convert_every_year(parameters, years):
    """The conversion as it was: write every year in ``years``."""
    for param in parameters.get_descendants():
        if isinstance(param, Parameter):
            if (param.metadata or {}).get("preserve_calendar_dates", False):
                continue
            blend = (param.metadata or {}).get("fiscal_year_blend", False)
            values = {}
            for year in years:
                value = fiscal_year_average(param, year) if blend else None
                if value is None:
                    value = param(f"{year}-04-30")
                values[year] = value
            for year, value in values.items():
                param.update(period=f"{year}", value=value)
    return parameters


def same(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a):
        return math.isnan(b)
    return type(a) is type(b) and a == b


def dates(*params) -> list:
    """Every date either parameter changes on.

    Values change only on these dates, so two parameters that agree on all
    of them agree on every date.
    """
    return sorted({value.instant_str for p in params for value in p.values_list})


def at(param, date: str):
    """The value on ``date``, looked up as policyengine-core does.

    Some parameters are dated 0000-01-01, which the public lookup cannot
    parse into an instant.
    """
    return param._get_at_instant(date)


def last_dated_year(param) -> int:
    return max(int(value.instant_str[:4]) for value in param.values_list)


def fiscal_year_value(param, year):
    blend = (param.metadata or {}).get("fiscal_year_blend", False)
    value = fiscal_year_average(param, year) if blend else None
    if value is None:
        value = param(f"{year}-04-30")
    return value


@pytest.fixture(scope="module")
def unconverted_gov():
    """The processed ``gov`` tree as it stands just before conversion."""
    system = tax_benefit_system.CountryTaxBenefitSystem()
    system.reset_parameters()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            tax_benefit_system, "convert_to_fiscal_year_parameters", lambda gov: gov
        )
        system.process_parameters()
    return system.parameters.gov


def converted_pairs(gov):
    converted = convert_to_fiscal_year_parameters(gov.clone())
    originals = {p.name: p for p in gov.get_descendants() if isinstance(p, Parameter)}
    for param in converted.get_descendants():
        if isinstance(param, Parameter):
            yield originals[param.name], param


def test_every_year_holds_its_fiscal_year_value(unconverted_gov):
    """Checked to five years past each parameter's last dated value."""
    checked = 0
    for original, converted in converted_pairs(unconverted_gov):
        if (original.metadata or {}).get("preserve_calendar_dates", False):
            continue
        for year in range(FIRST_FISCAL_YEAR, last_dated_year(original) + 6):
            expected = fiscal_year_value(original, year)
            for date in ("01-01", "04-05", "04-06", "12-31"):
                assert same(converted(f"{year}-{date}"), expected), (
                    original.name,
                    year,
                    date,
                )
            checked += 1

    assert checked > 20_000


def test_matches_writing_every_year(unconverted_gov):
    """Differential: the old write-every-year conversion, run past the data."""
    last_year = max(
        last_dated_year(p)
        for p in unconverted_gov.get_descendants()
        if isinstance(p, Parameter) and p.values_list
    )
    reference = convert_every_year(
        unconverted_gov.clone(), range(FIRST_FISCAL_YEAR, last_year + 2)
    )
    references = {
        p.name: p for p in reference.get_descendants() if isinstance(p, Parameter)
    }

    for _, converted in converted_pairs(unconverted_gov):
        expected = references[converted.name]
        for date in dates(converted, expected):
            assert same(at(converted, date), at(expected, date)), (
                converted.name,
                date,
            )


def test_the_state_pension_is_on_fiscal_years_past_2040(unconverted_gov):
    """Uprating dates it on 1 January after 2026, where the two coincide."""
    for original, converted in converted_pairs(unconverted_gov):
        if original.name == "gov.dwp.state_pension.new_state_pension.amount":
            for year in (2026, 2040, 2041, 2060):
                assert converted(str(year)) == original(f"{year}-04-30")
            return
    pytest.fail("new State Pension amount not found")


def test_parameters_dated_only_on_1_january_are_left_as_they_were(
    unconverted_gov,
):
    untouched = 0
    for original, converted in converted_pairs(unconverted_gov):
        if all(value.instant_str[4:] == "-01-01" for value in original.values_list):
            if (original.metadata or {}).get("fiscal_year_blend", False):
                continue
            assert [
                (value.instant_str, value.value) for value in converted.values_list
            ] == [(value.instant_str, value.value) for value in original.values_list]
            untouched += 1

    # Every index and growth series, and the parameters uprated by them.
    assert untouched > 100


def test_every_converted_parameter_is_marked_modified(unconverted_gov):
    for original, converted in converted_pairs(unconverted_gov):
        if (original.metadata or {}).get("preserve_calendar_dates", False):
            assert converted.modified == original.modified, converted.name
        else:
            assert converted.modified, converted.name


# Generated parameters: dates from 2010 to 2060, weighted to 1 January and to
# the April dates UK rates change on.
days = st.one_of(
    st.just((1, 1)),
    st.sampled_from([(4, 1), (4, 5), (4, 6), (4, 30), (5, 1), (10, 30), (12, 31)]),
    st.tuples(st.integers(1, 12), st.integers(1, 28)),
)
values = st.one_of(
    st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    st.integers(min_value=-1000, max_value=1000),
    st.just(float("inf")),
)


@st.composite
def parameters(draw):
    dated = {}
    for _ in range(draw(st.integers(min_value=1, max_value=12))):
        year = draw(st.integers(min_value=2010, max_value=2060))
        month, day = draw(days)
        dated[f"{year}-{month:02d}-{day:02d}"] = draw(values)
    metadata = {}
    if draw(st.booleans()):
        metadata["fiscal_year_blend"] = True
    return ParameterNode("root", data={"p": {"values": dated, "metadata": metadata}})


@settings(max_examples=300, deadline=None)
@given(node=parameters())
def test_generated_parameters_match_writing_every_year(node):
    reference = convert_every_year(node.clone(), range(FIRST_FISCAL_YEAR, 2062))
    converted = convert_to_fiscal_year_parameters(node.clone())

    for date in dates(converted.p, reference.p) + ["2061-01-01", "2100-06-01"]:
        assert same(at(converted.p, date), at(reference.p, date)), date


@settings(max_examples=300, deadline=None)
@given(node=parameters())
def test_generated_parameters_hold_fiscal_year_values_every_year(node):
    original = node.p
    converted = convert_to_fiscal_year_parameters(node.clone()).p

    for year in range(FIRST_FISCAL_YEAR, 2100):
        expected = fiscal_year_value(original, year)
        assert same(converted(f"{year}-01-01"), expected), year
        assert same(converted(f"{year}-12-31"), expected), year
    assert converted.modified
