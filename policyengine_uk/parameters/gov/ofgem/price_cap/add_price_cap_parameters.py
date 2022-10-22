from policyengine_core.parameters import ParameterNode, Parameter


def add_price_cap_parameters(
    parameters: ParameterNode,
    start_year: 2022,
    start_quarter: 4,
    end_year: 2023,
    end_quarter: 4,
) -> ParameterNode:
    """Add price cap parameters to the parameters tree.

    Args:
        parameters (ParameterNode): The parameters tree.
        start_year (int): The start year of the price cap.
        start_quarter (int): The start quarter of the price cap.
        end_year (int): The end year of the price cap.
        end_quarter (int): The end quarter of the price cap.

    Returns:
        ParameterNode: The parameters tree with price cap parameters added.
    """

    price_cap: ParameterNode = parameters.gov.ofgem.price_cap

    for year in range(start_year, end_year + 1):
        for quarter in range(1, 5):
            if year == start_year and quarter < start_quarter:
                continue
            if year == end_year and quarter > end_quarter:
                break
            name = f"{year}_q{quarter}"
            value = price_cap.base(f"{year}-{quarter * 3 - 2:02}-01")
            new_parameter = Parameter(
                name=name,
                data=dict(
                    description=f"Default tariff price cap for the average household in {year} Q{quarter}.",
                    values={
                        "0000-01-01": value,
                    },
                    metadata=dict(
                        name=f"ofgem_price_cap_{name}",
                        label=f"Ofgem energy price cap ({year} Q{quarter})",
                        unit="currency-GBP",
                        period="year",
                    ),
                ),
            )
            new_parameter.name = "gov.ofgem.price_cap." + new_parameter.name
            price_cap.add_child(
                name,
                new_parameter,
            )

    return parameters
