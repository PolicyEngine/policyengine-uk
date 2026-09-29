"""Build the uprating index of the Universal Credit standard allowance.

The Universal Credit Act 2025 s1 takes the standard allowance out of the
Social Security Administration Act 1992 s150 review for 2026-27 to 2029-30
and sets a minimum instead. Step 1 takes the 2025-26 amounts (then each
year the previous year's Step 2 amounts), Step 2 raises them by September
CPI (zero if prices fell) and Step 3 adds the year's uplift: 2.3%, 3.1%,
4.0% and 4.8%. The uplift does not compound: each year's amount is the
September CPI path from 2025-26 times 1 + that year's uplift. April 2026
reproduces the published £424.90 for a single claimant aged 25 or over:
£400.14 x 1.038 x 1.023. From 2030-31 s150 applies again, so the 2029-30
amount rises by September CPI and the 4.8% carries forward.

``gov.dwp.universal_credit.standard_allowance.uprating_index`` is the
September CPI index times 1 + the uplift in force in April of each year
(``gov.dwp.universal_credit.rebalancing.standard_allowance_uplift``, zero
while ``rebalancing.active`` is false). The standard allowance names it as
its uprating, so each year after the last published amount rises by
September CPI and by the change in the uplift.
"""

from policyengine_core.parameters import Parameter, ParameterNode


def add_uc_standard_allowance_uprating(parameters: ParameterNode) -> ParameterNode:
    """Add ``gov.dwp.universal_credit.standard_allowance.uprating_index``.

    Runs after ``create_economic_assumption_indices``, which builds the
    September CPI index this compounds.
    """
    september_cpi = parameters.gov.economic_assumptions.indices.september_cpi_uprating
    universal_credit = parameters.gov.dwp.universal_credit
    rebalancing = universal_credit.rebalancing
    values = {}
    for value in september_cpi.values_list:
        instant = f"{value.instant_str[:4]}-04-30"
        uplift = 0
        if rebalancing.active(instant):
            uplift = rebalancing.standard_allowance_uplift(instant) or 0
        values[value.instant_str] = value.value * (1 + uplift)
    index = Parameter(
        "gov.dwp.universal_credit.standard_allowance.uprating_index",
        data={
            "description": (
                "Uprating index of the Universal Credit standard allowance: "
                "September CPI with the Universal Credit Act 2025 uplift."
            ),
            "values": values,
            "metadata": {
                "unit": "/1",
                "label": "Universal Credit standard allowance uprating index",
            },
        },
    )
    universal_credit.standard_allowance.add_child("uprating_index", index)
    return parameters
