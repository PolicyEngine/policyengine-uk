import numpy as np
import pandas as pd
from survey_personal_incomes import SPI
from pathlib import Path
import shutil

DATA_STORE = Path(__file__).parent


class SPIDataset:
    def __init__(self, year: int):
        year = str(year)
        dataset_path = DATA_STORE / year
        if dataset_path.exists():
            person = pd.read_csv(dataset_path / "person.csv")
            benunit = pd.read_csv(dataset_path / "benunit.csv")
            household = pd.read_csv(dataset_path / "household.csv")
            self.entity_dfs = person, benunit, household
        else:
            self.entity_dfs = self.generate_dataset(year)

    def generate_dataset(self, year: int) -> None:
        """Generates a new FRS dataset.

        Args:
            year (int): The year of the FRS to use.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: The person, benefit unit and household datasets.
        """
        spi = SPI(year)

        person = spi.main
        person.columns = [col.upper() for col in person.columns]
        ids = np.arange(len(person))
        person["P_person_id"] = ids
        person["P_benunit_id"] = ids
        person["P_household_id"] = ids
        weight = spi.main.FACT
        person["P_FACT"] = weight

        person["P_role"] = "adult"

        benunit = pd.DataFrame(dict(B_person_id=ids, B_benunit_id=ids))

        household = pd.DataFrame(dict(H_household_id=ids))

        benunit["B_FACT"] = weight
        household["H_FACT"] = weight

        # store dataset for future use

        dataset_path = DATA_STORE / year

        if dataset_path.exists():
            shutil.rmtree(dataset_path)

        dataset_path.mkdir()
        person.to_csv(dataset_path / "person.csv", index=False)
        benunit.to_csv(dataset_path / "benunit.csv", index=False)
        household.to_csv(dataset_path / "household.csv", index=False)

        return person, benunit, household
