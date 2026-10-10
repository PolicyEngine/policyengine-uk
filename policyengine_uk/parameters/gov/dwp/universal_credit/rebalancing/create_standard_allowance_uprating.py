"""Build the uprating index for the Universal Credit standard allowance.

Universal Credit Act 2025 s. 1 sets minimum standard allowance amounts for
tax years 2026-27 to 2029-30 in three steps:

1. Take the 2025-26 amounts for 2026-27, and the previous year's Step 2
   amounts for each later year.
2. Increase them by the relevant CPI percentage, never below 0% (s. 1(3)).
3. Increase the result by the relevant uplift percentage for the year: 2.3%,
   3.1%, 4.0% and 4.8% (s. 1(4)).

Each uplift is measured against the CPI-only path from 2025-26, not compounded
on the previous uplift, because Step 1 takes the previous year's amount before
its Step 3. From one year to the next the allowance therefore grows by CPI
times (1 + this year's uplift) / (1 + last year's uplift).

The 2026-27 amounts are written into ``standard_allowance/amount.yaml`` as
legislated. That file is uprated by the index built here,
``gov.dwp.universal_credit.standard_allowance.uprating``: the benefit uprating
index ``gov.benefit_uprating_cpi``, with s. 1(3)'s 0% floor in 2026-27 to
2029-30, times (1 + that year's uplift). Uprating the 2026-27 amounts by it
gives each later year's amount the CPI growth and the change in uplift. After
2029-30 the uplift stays at 4.8%, so the allowance grows with CPI alone. The
benefit index is the model's measure of CPI for benefit uprating; s. 1(3)
names September CPI. Because it is the same index, the difference from a
CPI-only path is exactly the uplift.

A legislated amount in ``amount.yaml`` for 2026-27 to 2029-30 includes that
year's uplift from the s. 1(4) table. If the uplift in force differs (a
reform, or ``rebalancing.active`` false, which means no uplift), the amount is
rescaled by (1 + uplift in force) / (1 + legislated uplift), so every year's
allowance carries the uplift in force and keeps the CPI growth already in the
legislated rate. Only entries loaded from ``amount.yaml`` are rescaled; an
amount set by a reform, even one equal to the legislated amount, is used as
given.

This runs in ``process_parameters`` before uprating, so a parameter change
made through ``Scenario(parameter_changes=...)``, which re-runs that pipeline,
reaches the allowance. A ``reform=`` dict applied after processing does not
re-run uprating; set ``standard_allowance.amount`` directly instead.
"""

from policyengine_core.parameters import Parameter, ParameterNode, get_parameter

INDEX_NAME = "gov.dwp.universal_credit.standard_allowance.uprating"
# Universal Credit Act 2025 s. 1(1): tax years 2026-27 to 2029-30.
FIRST_ACT_YEAR = 2026
LAST_ACT_YEAR = 2029
# s. 1(4): the uplift included in a legislated amount for each tax year.
LEGISLATED_UPLIFT = {2026: 0.023, 2027: 0.031, 2028: 0.040, 2029: 0.048}
# Marks an amount entry already rescaled, so processing twice cannot rescale
# it again.
RESCALED = "_rescaled_to_uplift_in_force"


def tax_year_instant(year: int) -> str:
    """Date at which policy parameters are read for the tax year from April
    ``year``: 30 April, the date fiscal-year conversion samples."""
    return f"{year}-04-30"


def uplift_in_force(rebalancing: ParameterNode, year: int) -> float:
    instant = tax_year_instant(year)
    if not rebalancing.active(instant):
        return 0.0
    uplift = rebalancing.standard_allowance_uplift(instant)
    # Nil before the uplift parameter starts (2025-26).
    return 0.0 if uplift is None else uplift


def legislated_tax_year(instant_str: str) -> int:
    """Tax year of a legislated amount. Rates are dated from the start of
    April, before the 6 April start of the tax year they apply to."""
    year, month = int(instant_str[:4]), int(instant_str[5:7])
    return year if month >= 4 else year - 1


def benefit_index_values(parameters: ParameterNode) -> dict:
    """``gov.benefit_uprating_cpi`` for each year of its uprating index, as
    uprating will extend it: its own values up to its latest one, then that
    value moved with its uprating index. Each year is read on 30 April, the
    date fiscal-year conversion samples, so a reform to the benefit index for
    a fiscal year reaches that year. Keyed by 1 January, as the index is."""
    benefit_index = parameters.gov.benefit_uprating_cpi
    cpi_index = get_parameter(parameters, benefit_index.metadata["uprating"])
    last_instant = benefit_index.values_list[0].instant_str
    value_at_last = benefit_index(last_instant)
    cpi_at_last = cpi_index(last_instant)
    values = {}
    for entry in sorted(cpi_index.values_list, key=lambda e: e.instant_str):
        instant = tax_year_instant(int(entry.instant_str[:4]))
        if instant <= last_instant or cpi_at_last is None:
            values[entry.instant_str] = benefit_index(instant)
        else:
            values[entry.instant_str] = value_at_last * cpi_index(instant) / cpi_at_last
    return values


def add_uc_standard_allowance_uprating(parameters: ParameterNode) -> ParameterNode:
    universal_credit = parameters.gov.dwp.universal_credit
    rebalancing = universal_credit.rebalancing
    standard_allowance = universal_credit.standard_allowance

    for amount in standard_allowance.amount.get_descendants():
        if not isinstance(amount, Parameter):
            continue
        for value in amount.values_list:
            year = legislated_tax_year(value.instant_str)
            # Entries loaded from amount.yaml carry its path; entries a reform
            # writes do not.
            if (
                year in LEGISLATED_UPLIFT
                and value.value is not None
                and value.file_path is not None
                and not getattr(value, RESCALED, False)
            ):
                value.value *= (1 + uplift_in_force(rebalancing, year)) / (
                    1 + LEGISLATED_UPLIFT[year]
                )
                setattr(value, RESCALED, True)

    values = {}
    cpi_path = 1.0
    previous_cpi = None
    for instant, cpi in benefit_index_values(parameters).items():
        year = int(instant[:4])
        if cpi is None:
            continue
        if previous_cpi is not None:
            growth = cpi / previous_cpi
            if FIRST_ACT_YEAR <= year <= LAST_ACT_YEAR:
                growth = max(1.0, growth)
            cpi_path *= growth
        previous_cpi = cpi
        values[instant] = cpi_path * (1 + uplift_in_force(rebalancing, year))

    standard_allowance.add_child(
        "uprating",
        Parameter(
            name=INDEX_NAME,
            data={
                "description": (
                    "Uprating index for the Universal Credit standard "
                    "allowance: benefit uprating CPI times one plus the "
                    "Universal Credit Act 2025 uplift."
                ),
                "values": values,
                "metadata": {
                    "unit": "/1",
                    "label": "Universal Credit standard allowance uprating index",
                    "reference": [
                        {
                            "title": "Universal Credit Act 2025 s. 1",
                            "href": "https://www.legislation.gov.uk/ukpga/2025/22/section/1",
                        }
                    ],
                },
            },
        ),
    )
    return parameters
