from pathlib import Path
import pandas as pd
import numpy as np
from argparse import ArgumentParser
import shutil

ID_COLS = (
    "P_sernum",
    "P_BENUNIT",
    "P_PERSON",
    "B_sernum",
    "B_BENUNIT",
    "H_sernum",
    "P_person_id",
    "P_benunit_id",
    "P_household_id",
    "B_benunit_id",
    "B_household_id",
    "H_household_id",
)


def export_synthetic_frs(year: int) -> None:
    dataset_path = (
        Path(__file__).parent.parent / "microdata" / "frs" / str(year)
    )
    person = pd.read_csv(dataset_path / "person.csv")
    benunit = pd.read_csv(dataset_path / "benunit.csv")
    household = pd.read_csv(dataset_path / "household.csv")
    output_folder = dataset_path.parent / (str(year) + "_anon")
    if output_folder.exists():
        shutil.rmtree(output_folder)
    output_folder.mkdir()
    anonymise(person).to_csv(output_folder / "person.csv")
    anonymise(benunit).to_csv(output_folder / "benunit.csv")
    anonymise(household).to_csv(output_folder / "household.csv")


def anonymise(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for col in result.columns:
        if col not in ID_COLS:
            # don't change identity columns, this breaks structures
            if result[col].unique().size < 16:
                # shuffle categorical columns
                result[col] = result[col].sample(len(result))
            else:
                # shuffle + add noise to numeric columns
                # noise = between -3% and +3% added to each row
                noise = np.random.rand() * 3e-2 + 1.0
                result[col] = result[col].sample(len(result)) * noise
    return result


if __name__ == "__main__":
    parser = ArgumentParser(
        description="A utility to generate functional anonymised datasets in the same format as the FRS."
    )
    parser.add_argument(
        "year", type=int, help="The year of the FRS to anonymise"
    )
    args = parser.parse_args()
    export_synthetic_frs(args.year)
