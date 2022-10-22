import os
from policyengine_uk import REPO, parameters
from policyengine_uk.tools.simulation import Microsimulation
import h5py

BENEFITS = [
    "universal_credit",
    "pension_credit",
    "child_benefit",
    "working_tax_credit",
    "child_tax_credit",
    "income_support",
    "housing_benefit",
    "JSA_income",
]

YEARS = list(range(2022, 2026))


def add_takeup_parameters():
    """
    Calculate simulation-based benefit takeup parameters and prints them.
    """

    from policyengine_uk import Microsimulation

    baseline = Microsimulation()
    full_benefit_claimants = Microsimulation()
    for year in YEARS:
        full_benefit_claimants.set_input(
            "claims_all_entitled_benefits",
            year,
            [True] * len(baseline.calc("benunit_id", period=year)),
        )

    takeup_parameters = [
        parameters.benefit.universal_credit.takeup,
        parameters.gov.dwp.pension_credit.takeup,
        parameters.gov.hmrc.child_benefit.takeup,
        parameters.gov.dwp.tax_credits.working_tax_credit.takeup,
        parameters.gov.dwp.tax_credits.child_tax_credit.takeup,
        parameters.gov.dwp.income_support.takeup,
        parameters.gov.dwp.housing_benefit.takeup,
        parameters.gov.dwp.JSA.income.takeup,
    ]

    for variable, parameter in zip(BENEFITS, takeup_parameters):
        parameter.values_list = []
        print(f"{variable}:")
        for year in YEARS:
            baseline_claimants = (
                baseline.calc(variable, period=year) > 0
            ).sum()
            maximum_claimants = (
                full_benefit_claimants.calc(variable, period=year) > 0
            ).sum()
            takeup_rate = round(baseline_claimants / maximum_claimants, 4)
            print(
                f"\t{year}: {baseline_claimants/1e6:.2f}m / {maximum_claimants/1e6:.2f}m = {takeup_rate:.1%}"
            )
            parameter.update(
                value=takeup_rate,
                period=f"year:{year}:1",
            )

    print("PARAMETERS:")
    for parameter in takeup_parameters:
        print(f"\t{parameter.name}: \n{parameter}\n\n")


if __name__ == "__main__":
    add_takeup_parameters()
