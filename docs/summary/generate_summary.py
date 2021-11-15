from argparse import ArgumentParser
from openfisca_uk import Microsimulation
from openfisca_uk_data import FRS
import yaml
from rdbl import num

def main():
    sim = Microsimulation(dataset=FRS)
    year = 2022

    percentage = lambda x: f"{round(x * 100, 2)}%"

    results = {
        "Poverty rate (BHC)": percentage(sim.calc('in_poverty_bhc', map_to='person', period=year).mean()),
        "Poverty rate (AHC)": percentage(sim.calc('in_poverty_ahc', map_to='person', period=year).mean()),
        "Income Tax revenue": num(sim.calc("income_tax", period=year).sum()),
        "National Insurance (employee-side) revenue": num(sim.calc("national_insurance", period=year).sum()),
        "Employment income": num(sim.calc("employment_income", period=year).sum()),
        "Total income": num(sim.calc("total_income", period=year).sum()),
        "Benefit expenditure": num(sim.calc("benefits", period=year).sum()),
    }

    with open("docs/summary/summary.yaml", "w+") as f:
        yaml.dump(results, f)
    

if __name__ == "__main__":
    parser = ArgumentParser(description="Generate a summary of the tax-benefit system")
    args = parser.parse_args()
    main()