"""Build the uprating index for the Universal Credit LCWRA element.

Universal Credit Act 2025 s. 3(1):

    Subsections (1) and (2) of section 150 of the Social Security
    Administration Act 1992 (annual up-rating of benefits) do not apply, in
    the tax years ending with 5 April 2026, 5 April 2027, 5 April 2028 and
    5 April 2029, to the LCWRA element or the LCW element.

SSAA 1992 s. 150(1) has the Secretary of State review the Universal Credit
amounts (s. 150(1)(n)) in each tax year, and s. 150(2) provides for an
up-rating order where prices have risen; for these amounts the increase is
at the Secretary of State's discretion (s. 150(2)(b)), as s. 150(3) does not
list them. An order brings its changes into force in the week beginning with
the first Monday of the tax year after the one in which it is made
(s. 150(10)(a)(i)), for Universal Credit from the first assessment period
beginning on or after that day (s. 150(10ZA) and (10ZB)). The four
disapplied reviews, in 2025-26 to 2028-29, are therefore those that would
have uprated the rates for 2026-27 to 2029-30, the years named in the
section's heading. The review in 2029-30 is not disapplied, so the element
can rise again from April 2030.

``elements/disabled/amount.yaml`` holds the 2026-27 amount set by s. 2
(£217.26 a month) and is uprated by the index built here,
``gov.dwp.universal_credit.elements.disabled.uprating``. The index moves
with ``gov.benefit_uprating_cpi``, the model's benefit uprating index, as
uprating will extend it (including any reform to it), except in a tax year
in which ``rebalancing.health_element_freeze`` and ``rebalancing.active`` are
both true, when it stays at the previous year's value. It never falls, as
s. 150(2) provides only for increases. Uprating an amount by it therefore
holds the amount through the frozen years and then raises it by each later
year's increase in the benefit index, from the frozen amount rather than
with the frozen years' increases added back.

The pre-2026 (protected) amount of the element is also frozen by s. 3 and
raised under s. 4; ``scenarios/uc_reform.py`` sets it for 2026-27 to
2029-30. The LCW element is not modelled.

This runs in ``process_parameters`` before uprating, so a change made through
``Scenario(parameter_changes=...)``, which re-runs that pipeline, reaches the
element: to the freeze, to ``rebalancing.active``, to the benefit index or
the forecasts behind it, or to the amount itself, which is then held or
uprated from the changed value. A ``reform=`` dict is applied after
processing and does not re-run uprating; it changes the years it names.
"""

from typing import Dict

from policyengine_core.parameters import Parameter, ParameterNode, get_parameter

INDEX_NAME = "gov.dwp.universal_credit.elements.disabled.uprating"
BENEFIT_INDEX_NAME = "gov.benefit_uprating_cpi"
# Fiscal-year conversion reads each tax year's value at 30 April.
FISCAL_YEAR_SAMPLE_MONTH_DAY = "04-30"
# Index values are keyed to 1 January, as core uprating keys its values.
INDEX_VALUE_MONTH_DAY = "01-01"


def tax_year_instant(year: int) -> str:
    """Date at which parameters are read for the tax year from April
    ``year``."""
    return f"{year}-{FISCAL_YEAR_SAMPLE_MONTH_DAY}"


def latest_instant(parameter: Parameter) -> str:
    return max(value.instant_str for value in parameter.values_list)


def uprating_parameter_name(parameter: Parameter):
    """Name of the parameter that uprates ``parameter``, or None."""
    meta = parameter.metadata.get("uprating")
    if meta is None:
        return None
    if isinstance(meta, str):
        return meta
    if set(meta) != {"parameter"}:
        raise NotImplementedError(
            f"{parameter.name} is uprated with options {sorted(meta)}; the "
            "Universal Credit health element uprating reads it only as a "
            "plain uprating index."
        )
    return meta["parameter"]


def projected_value(parameter: Parameter, parameters: ParameterNode, at: str):
    """``parameter`` at ``at`` as core uprating will extend it.

    Core uprating starts from the latest stated value and adds, for each
    value of the uprating index dated after it, that value times the index's
    change since the latest stated date. Read before uprating runs, the
    parameter itself holds only its stated values.
    """
    last = latest_instant(parameter)
    uprater_name = uprating_parameter_name(parameter)
    if at <= last or uprater_name is None:
        return parameter(at)
    uprater = get_parameter(parameters, uprater_name)
    if uprating_parameter_name(uprater) is not None:
        raise NotImplementedError(
            f"{uprater.name}, which uprates {parameter.name}, is itself "
            "uprated; the Universal Credit health element uprating reads "
            "only a fully stated index."
        )
    projected = [
        value.instant_str
        for value in uprater.values_list
        if last < value.instant_str <= at
    ]
    if not projected:
        return parameter(at)
    return parameter(last) * uprater(max(projected)) / uprater(last)


def index_years(parameters: ParameterNode) -> range:
    """Years the benefit index covers once uprated: its own stated years and
    those of the index that uprates it."""
    benefit_index = get_parameter(parameters, BENEFIT_INDEX_NAME)
    instants = [value.instant_str for value in benefit_index.values_list]
    uprater_name = uprating_parameter_name(benefit_index)
    if uprater_name is not None:
        uprater = get_parameter(parameters, uprater_name)
        instants += [value.instant_str for value in uprater.values_list]
    years = [int(instant[:4]) for instant in instants]
    return range(min(years), max(years) + 1)


def is_frozen(rebalancing: ParameterNode, year: int) -> bool:
    """Whether the element keeps the previous year's amount in the tax year
    from April ``year``. A year before either parameter starts is not."""
    instant = tax_year_instant(year)
    return bool(rebalancing.health_element_freeze(instant)) and bool(
        rebalancing.active(instant)
    )


def health_element_index_values(parameters: ParameterNode) -> Dict[str, float]:
    """The uprating index, keyed to 1 January of each year."""
    benefit_index = get_parameter(parameters, BENEFIT_INDEX_NAME)
    rebalancing = parameters.gov.dwp.universal_credit.rebalancing
    values = {}
    index = 1.0
    previous = None
    for year in index_years(parameters):
        current = projected_value(benefit_index, parameters, tax_year_instant(year))
        if current is None:
            continue
        if previous is not None and not is_frozen(rebalancing, year):
            index *= max(1.0, current / previous)
        previous = current
        values[f"{year}-{INDEX_VALUE_MONTH_DAY}"] = index
    return values


def add_uc_health_element_uprating(parameters: ParameterNode) -> ParameterNode:
    """Add ``gov.dwp.universal_credit.elements.disabled.uprating``.

    Runs after ``create_economic_assumption_indices``, which builds the index
    that extends ``gov.benefit_uprating_cpi``.
    """
    parameters.gov.dwp.universal_credit.elements.disabled.add_child(
        "uprating",
        Parameter(
            INDEX_NAME,
            data={
                "description": (
                    "Uprating index for the Universal Credit LCWRA element: "
                    "the benefit uprating index, held flat in the tax years "
                    "for which the Universal Credit Act 2025 freezes the "
                    "element and never falling."
                ),
                "values": health_element_index_values(parameters),
                "metadata": {
                    "unit": "/1",
                    "label": "Universal Credit health element uprating index",
                    "reference": [
                        {
                            "title": "Universal Credit Act 2025 s. 3",
                            "href": "https://www.legislation.gov.uk/ukpga/2025/22/section/3",
                        },
                        {
                            "title": "Social Security Administration Act 1992 s. 150",
                            "href": "https://www.legislation.gov.uk/ukpga/1992/5/section/150",
                        },
                    ],
                },
            },
        ),
    )
    return parameters
