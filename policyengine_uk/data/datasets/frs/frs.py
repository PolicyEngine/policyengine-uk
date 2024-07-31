import pandas as pd
from policyengine_core.data import Dataset
from policyengine_uk.data.storage import STORAGE_FOLDER
from pathlib import Path
import numpy as np
import warnings

warnings.filterwarnings("ignore")

class FRS(Dataset):
    frs_tab_folder: str
    data_format = Dataset.FLAT_FILE

    def generate(self):
        frs_folder = Path(self.frs_tab_folder)
        adult = pd.read_csv(frs_folder / 'adult.tab', sep='\t')
        adult.columns = adult.columns.str.lower()
        child = pd.read_csv(frs_folder / 'child.tab', sep='\t')
        child.columns = child.columns.str.lower()

        df = pd.DataFrame()

        # First, initialise.
        # Adults, followed by children
        df["is_child"] = np.empty(len(adult), dtype=bool)
        df["is_child"] = True
        df["is_child"][:len(adult)] = False
        children = df.is_child
        adults = ~children

        # Add ID variables

        df["person_id"] = df.index
        df["person_benefit_unit_id"] = pd.concat([adult.sernum * 10 + adult.benunit, child.sernum * 10 + child.benunit], ignore_index=True)
        df["person_household_id"] = pd.concat([adult.sernum, child.sernum], ignore_index=True)

        df.to_csv(self.file_path, index=False)

class FRS_2022_23(FRS):
    frs_tab_folder = "~/ukda/frs_2022_23"
    file_path = STORAGE_FOLDER / "frs_2022_23.csv"
    label = "FRS (2022-23)"
    name = "frs_2022_23"