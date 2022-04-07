from openfisca_uk.microdata.utils import *
from openfisca_uk.microdata.datasets.frs.frs_enhanced import FRSEnhanced
import shutil
import pandas as pd
import numpy as np
import h5py
import requests
from tqdm import tqdm

DEFAULT_SYNTH_FILE = "https://github.com/PolicyEngine/openfisca-uk-data/releases/download/synth-frs-2019/synth_frs_2019.h5"


@dataset
class SynthFRS:
    name = "synth_frs"
    model = UK

    def generate(year):
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

        data = FRSEnhanced.load(year)
        year = int(year)

        with h5py.File(SynthFRS.file(year), mode="w") as f:
            for variable in data.keys():
                try:
                    f[variable] = anonymise(data[variable], variable)
                except:
                    f[variable] = anonymise(data[variable], variable).astype(
                        "S"
                    )

    def download(year: int = 2019):
        if year == 2018:
            SynthFRS.save(
                "https://github.com/PolicyEngine/openfisca-uk-data/releases/download/synth-frs/synth_frs_2018.h5",
                2018,
            )
        elif year == 2019:
            SynthFRS.save(
                "https://github.com/PolicyEngine/openfisca-uk-data/releases/download/synth-frs-2019/synth_frs_2019.h5",
                2019,
            )
