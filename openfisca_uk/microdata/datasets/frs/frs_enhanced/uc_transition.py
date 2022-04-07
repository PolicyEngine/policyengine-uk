from typing import Dict
from openfisca_uk.microdata.datasets.frs.frs import FRS
from numpy.typing import ArrayLike

LEGACY_BENEFITS = [
    "working_tax_credit",
    "child_tax_credit",
    "housing_benefit",
    "income_support",
    "ESA_income",
    "JSA_income",
]


def migrate_to_universal_credit(
    dataset: type = FRS, year: int = 2019
) -> Dict[str, ArrayLike]:
    """Converts legacy benefit claimants to Universal Credit claimants by switching
    reported amounts.

    Args:
        dataset (type, optional): The dataset to use. Defaults to FRS.
        year (int, optional): The year to use. Defaults to 2019.

    Returns:
        Dict[str, ArrayLike]: Variables with replaced values.
    """
    from openfisca_uk import Microsimulation

    frs = Microsimulation(
        dataset=dataset,
        year=year,
        adjust_weights=False,
        add_baseline_values=False,
    )

    changes = {
        "universal_credit_reported": frs.calc(
            "universal_credit_reported", period=year
        ).values
    }

    for benefit in LEGACY_BENEFITS:
        reported_amount = frs.calc(benefit + "_reported", period=year).values
        changes[benefit + "_reported"] = reported_amount * 0
        changes["universal_credit_reported"] += reported_amount

    return changes
