from typing import Dict
from policyengine_uk.data.datasets.frs.frs import FRS
from numpy.typing import ArrayLike
from policyengine_core.data.dataset import Dataset

LEGACY_BENEFITS = [
    "working_tax_credit",
    "child_tax_credit",
    "housing_benefit",
    "income_support",
    "ESA_income",
    "JSA_income",
]


def migrate_to_universal_credit(
    dataset: Dataset = FRS, year: int = 2022
) -> Dict[str, ArrayLike]:
    """Converts legacy benefit claimants to Universal Credit claimants by switching
    reported amounts.

    Args:
        dataset (type, optional): The dataset to use. Defaults to FRS.
        year (int, optional): The year to use. Defaults to 2022.

    Returns:
        Dict[str, ArrayLike]: Variables with replaced values.
    """
    from policyengine_uk import Microsimulation

    frs = Microsimulation(
        dataset=dataset,
        year=year,
    )

    changes = {
        f"universal_credit_reported/{year}": frs.calc(
            "universal_credit_reported", period=year
        ).values
    }

    for benefit in LEGACY_BENEFITS:
        reported_amount = frs.calc(benefit + "_reported", period=year).values
        changes[f"{benefit}_reported/{year}"] = reported_amount * 0
        changes[f"universal_credit_reported/{year}"] += reported_amount

    return changes
