"""Growth of the UK totals a dataset can carry (policyengine-uk#2896).

A UK total sums a household column over all UK households at their weights.
Household weights grow with population, so the total grows with the column's
own growth and with population: (1 + column growth) x (1 + population growth)
- 1. The totals of corporate and private pension wealth, which grow with
per-capita GDP, therefore grow with nominal GDP; those of spending, which grows
with CPI, with CPI and population. Each series is generated before the index
pass, so it gets its index like any other.
"""

from policyengine_core.parameters import Parameter, ParameterNode

# Each generated series: the per-household growth it combines with population
# growth, and its label.
UK_TOTAL_GROWTH = {
    "per_capita_gdp": ("obr.per_capita.gdp", "UK total growth with per-capita GDP"),
    "consumer_price_index": ("obr.consumer_price_index", "UK total growth with CPI"),
}


def _years(parameter: Parameter) -> list:
    return [int(value.instant_str[:4]) for value in parameter.values_list]


def add_uk_total_growth(parameters: ParameterNode) -> ParameterNode:
    yoy_growth = parameters.gov.economic_assumptions.yoy_growth
    population = yoy_growth.ons.population
    node = ParameterNode(name="gov.economic_assumptions.yoy_growth.uk_totals", data={})
    for name, (path, label) in UK_TOTAL_GROWTH.items():
        per_household = yoy_growth.get_child(path)
        # From the first year both series cover. A series that ends early holds
        # its last rate, as the index pass reads it.
        first = max(min(_years(per_household)), min(_years(population)))
        last = max(max(_years(per_household)), max(_years(population)))
        values = {
            f"{year}-01-01": (1 + per_household(year)) * (1 + population(year)) - 1
            for year in range(first, last + 1)
        }
        node.add_child(
            name,
            Parameter(
                f"gov.economic_assumptions.yoy_growth.uk_totals.{name}",
                data={
                    "description": (
                        "Year-on-year growth of a UK total of a household "
                        f"column that grows with {path}: that growth and "
                        "population growth combined."
                    ),
                    "values": values,
                    "metadata": {
                        "unit": "/1",
                        "label": label,
                    },
                },
            ),
        )
    yoy_growth.add_child("uk_totals", node)
    return parameters
