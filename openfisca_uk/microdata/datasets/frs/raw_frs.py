from pathlib import Path
from typing import List
from openfisca_uk.microdata.utils import dataset
import pandas as pd
import shutil
from openfisca_uk.microdata.utils import DATA_DIR, safe_rmdir, data_folder
import re
from tqdm import tqdm
import h5py
import numpy as np
import warnings


@dataset
class RawFRS:
    name = "raw_frs"

    def generate(zipfile, year) -> None:
        folder = Path(zipfile)
        year = str(year)

        if not folder.exists():
            raise FileNotFoundError("Invalid path supplied.")

        new_folder = RawFRS.data_dir / "tmp"
        shutil.unpack_archive(folder, new_folder)
        folder = new_folder

        main_folder = next(folder.iterdir())
        tab_folder = main_folder / "tab"
        if tab_folder.exists():
            criterion = re.compile("[a-z]+\.tab")
            data_files = [
                path
                for path in tab_folder.iterdir()
                if criterion.match(path.name)
            ]
            task = tqdm(data_files, desc="Saving raw data tables")
            with pd.HDFStore(RawFRS.file(year)) as file:
                for filepath in task:
                    task.set_description(
                        f"Saving raw data tables ({filepath.name})"
                    )
                    table_name = filepath.name.replace(".tab", "")
                    df = pd.read_csv(
                        filepath, delimiter="\t", low_memory=False
                    ).apply(pd.to_numeric, errors="coerce")
                    df.columns = df.columns.str.upper()
                    if "PERSON" in df.columns:
                        df["person_id"] = (
                            df.SERNUM * 1e2 + df.BENUNIT * 1e1 + df.PERSON
                        ).astype(int)
                    if "BENUNIT" in df.columns:
                        df["benunit_id"] = (
                            df.SERNUM * 1e2 + df.BENUNIT * 1e1
                        ).astype(int)
                    if "SERNUM" in df.columns:
                        df["household_id"] = (df.SERNUM * 1e2).astype(int)
                    if table_name in ("adult", "child"):
                        df.set_index("person_id", inplace=True)
                    elif table_name == "benunit":
                        df.set_index("benunit_id", inplace=True)
                    elif table_name == "househol":
                        df.set_index("household_id", inplace=True)
                    file[table_name] = df
        else:
            raise FileNotFoundError("Could not find the TAB files.")

        tmp_folder = RawFRS.data_dir / "tmp"
        if tmp_folder.exists():
            safe_rmdir(tmp_folder)
