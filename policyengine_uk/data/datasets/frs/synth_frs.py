import logging
import numpy as np
from policyengine_core.data import Dataset, PublicDataset
import pandas as pd
import h5py
from policyengine_uk.data.datasets.frs.frs import FRS
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER


class SynthFRS(PublicDataset):
    name = "synth_frs"
    label = "Synthetic FRS"
    is_openfisca_compatible = True
    url_by_year = {
        2022: "https://github.com/PolicyEngine/openfisca-uk/releases/download/synth-frs-v1/synth_frs_2022.h5",
    }
    folder_path = policyengine_uk_MICRODATA_FOLDER

    format = Dataset.ARRAYS

    def generate(self, year: int):
        if year not in FRS.years:
            logging.warning(f"FRS for {year} not found: generating.")
            FRS.generate(year)

        ID_COLS = (
            "person_id",
            "person_benunit_id",
            "person_benunit_role",
            "person_household_id",
            "person_household_role",
            "person_state_id",
            "person_state_role",
            "benunit_id",
            "household_id",
            "state_id",
        )

        def anonymise(arr: np.array, name: str) -> pd.DataFrame:
            result = pd.Series(arr)
            if name not in ID_COLS:
                # don't change identity columns, this breaks structures
                if len(result.unique()) < 16:
                    # shuffle categorical columns
                    result = result.sample(frac=1).values
                else:
                    # shuffle + add noise to numeric columns
                    # noise = between -3% and +3% added to each row
                    noise = np.random.rand() * 3e-2 + 1.0
                    result = result.sample(frac=1).values * noise
            return result

        data = FRS.load(year)

        with h5py.File(SynthFRS.file(year), mode="w") as f:
            for variable in data.keys():
                try:
                    f[variable] = anonymise(data[variable], variable)
                except:
                    f[variable] = anonymise(data[variable], variable).astype(
                        "S"
                    )


SynthFRS = SynthFRS()
