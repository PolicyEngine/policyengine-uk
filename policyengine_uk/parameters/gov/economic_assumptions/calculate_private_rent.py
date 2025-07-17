from policyengine_core.parameters import Parameter, ParameterNode


def add_private_rent_growth(
    parameters: ParameterNode,
) -> ParameterNode:
    """
    Calculate private rent growth from OBR aggregate rent forecast using weighted decomposition.
    Uses England housing tenure weights (18.8% private, 16.4% social households).
    """
    obr = parameters.gov.economic_assumptions.yoy_growth.obr
    
    aggregate_rent = obr.rent
    
    # Get social rent growth (CPI + 1%, one year lagged)
    social_rent = obr.social_rent
    
    # From latest English Housing Survey data
    PRIVATE_RENTAL_HOUSEHOLDS = 0.188
    SOCIAL_RENTAL_HOUSEHOLDS = 0.164
    
    total_rental_households = PRIVATE_RENTAL_HOUSEHOLDS + SOCIAL_RENTAL_HOUSEHOLDS
    
    private_weight = PRIVATE_RENTAL_HOUSEHOLDS / total_rental_households
    social_weight = SOCIAL_RENTAL_HOUSEHOLDS / total_rental_households
    
    # Calculate private rent growth for each year
    private_rent_values = {}
    for year in range(2022, 2030):
        aggregate_growth = aggregate_rent(year)
        social_growth = social_rent(year)
        
        private_growth = (aggregate_growth - social_weight * social_growth) / private_weight
        private_rent_values[f"{year}-01-01"] = round(private_growth, 5)
    
    private_rent_parameter = Parameter(
        "gov.economic_assumptions.yoy_growth.obr.private_rent",
        data={
            "values": private_rent_values,
        },
    )
    
    obr.add_child(
        "private_rent",
        private_rent_parameter,
    )
    
    return parameters