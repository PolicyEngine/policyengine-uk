from argparse import ArgumentParser
from policyengine_uk import Microsimulation
from policyengine_uk.data import EnhancedFRS
import yaml
import subprocess


def percentage(x: float) -> str:
    return f"{round(x * 100, 2)}%"


def gbp(x: float) -> str:
    return f"{round(x / 1e9, 1):,}bn"


def main(args):
    with open("docs/summary/summary.yaml", "r") as f:
        previous_results = yaml.safe_load(f)

    sim = Microsimulation(dataset=EnhancedFRS, year=2022)
    year = 2022

    results = {
        "Poverty rate (BHC)": percentage(
            sim.calc("in_poverty_bhc", map_to="person", period=year).mean()
        ),
        "Poverty rate (AHC)": percentage(
            sim.calc("in_poverty_ahc", map_to="person", period=year).mean()
        ),
        "Income Tax revenue": gbp(sim.calc("income_tax", period=year).sum()),
        "National Insurance (employee-side) revenue": gbp(
            sim.calc("national_insurance", period=year).sum()
        ),
        "Total income": gbp(sim.calc("total_income", period=year).sum()),
        "Benefit expenditure": gbp(sim.calc("benefits", period=year).sum()),
    }

    for key, value in results.items():
        previous_value = previous_results.get(key, "")
        if previous_value != value:
            print(f"{key}: {previous_value} -> {value}")
        else:
            print(f"{key}: {value}")

    if args.save:
        with open("docs/summary/summary.yaml", "w") as f:
            yaml.safe_dump(results, f)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Generate a summary of the tax-benefit system."
    )
    parser.add_argument(
        "--save", action="store_true", help="Save the results."
    )
    args = parser.parse_args()
    main(args)
