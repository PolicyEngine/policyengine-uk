"""Tenure categories shared by household and benefit-unit rental flags."""


def is_renting_tenure(tenure):
    tenures = tenure.possible_values
    return (
        (tenure == tenures.RENT_PRIVATELY)
        | (tenure == tenures.RENT_FROM_COUNCIL)
        | (tenure == tenures.RENT_FROM_HA)
    )
