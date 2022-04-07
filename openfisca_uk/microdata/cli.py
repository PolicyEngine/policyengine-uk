from argparse import ArgumentParser
from openfisca_uk.microdata import *
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)


def main():
    datasets = {ds.name: ds for ds in DATASETS}
    parser = ArgumentParser(
        description="A utility for storing OpenFisca-UK-compatible microdata."
    )
    parser.add_argument("dataset", help="The dataset to select")
    parser.add_argument("action", help="The action to take")
    parser.add_argument(
        "args", nargs="*", help="The arguments to pass to the function"
    )
    args = parser.parse_args()
    if args.dataset == "datasets":
        if args.action == "list":
            return dataset_summary()
    else:
        try:
            return getattr(datasets[args.dataset], args.action)(*args.args)
        except Exception as e:
            print("\n\nEncountered an error:")
            raise e


def dataset_summary() -> str:
    years = list(sorted(list(set(sum([ds.years for ds in DATASETS], [])))))
    df = pd.DataFrame(
        {
            year: ["✓" if year in ds.years else "" for ds in DATASETS]
            for year in years
        },
        index=[ds.name for ds in DATASETS],
    )
    df = df.sort_values(by=list(df.columns[::-1]), ascending=False)
    return df.to_markdown(tablefmt="pretty")


if __name__ == "__main__":
    main()
