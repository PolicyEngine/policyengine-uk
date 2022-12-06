import re
import shutil
from policyengine_core.data import PrivateDataset
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER


class RawFRS(PrivateDataset):
    name = "raw_frs"
    label = "Raw FRS"
    folder_path = policyengine_uk_MICRODATA_FOLDER
    is_openfisca_compatible = False

    filename_by_year = {
        2019: "raw_frs_2019.h5",
    }

    def generate(self, year: int, ukds_tab_zipfile: str):
        """Generates the raw FRS tabular dataset from the TAB zip archive
        downloadable from the UKDS.

        Args:
            year (int): The year of the FRS to generate.
            ukds_tab_zipfile (str): The path to the TAB zip archive, or a folder containing the TAB files.
        """

        folder = Path(ukds_tab_zipfile)
        year = str(year)

        if not folder.exists():
            raise FileNotFoundError("Invalid path supplied.")
        if folder.is_dir() and len(list(folder.glob("*.tab"))) > 0:
            tab_folder = folder
        else:
            new_folder = self.folder_path / "tmp"
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

        tmp_folder = self.folder_path / "tmp"
        if tmp_folder.exists():
            shutil.rmtree(tmp_folder)


RawFRS = RawFRS()
