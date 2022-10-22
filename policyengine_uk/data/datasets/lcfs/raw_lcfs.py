import re
import shutil
from policyengine_core.data import PrivateDataset
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER


class RawLCFS(PrivateDataset):
    name = "raw_lcfs"
    label = "Raw LCFS"
    folder_path = policyengine_uk_MICRODATA_FOLDER
    is_openfisca_compatible = False

    filename_by_year = {
        2019: "raw_lcfs_2019.h5",
    }

    def generate(self, year: int, ukds_tab_zipfile: str):
        """Generates the raw LCFS tabular dataset from the TAB zip archive
        downloadable from the UKDS.

        Args:
            year (int): The year of the FRS to generate.
            ukds_tab_zipfile (str): The path to the TAB zip archive.
        """

        folder = Path(ukds_tab_zipfile)
        year = str(year)

        if not folder.exists():
            raise FileNotFoundError("Invalid path supplied.")

        new_folder = self.folder_path / "tmp"
        shutil.unpack_archive(folder, new_folder)
        folder = new_folder

        main_folder = next(folder.iterdir())
        tab_folder = main_folder / "tab"
        if tab_folder.exists():
            criterion = re.compile(".*\.tab")
            data_files = [
                path
                for path in tab_folder.iterdir()
                if criterion.match(path.name)
            ]
            task = tqdm(data_files, desc="Saving raw data tables")
            with pd.HDFStore(RawLCFS.file(year)) as file:
                for filepath in task:
                    task.set_description(
                        f"Saving raw data tables ({filepath.name})"
                    )
                    table_name = filepath.name.replace(".tab", "")
                    df = pd.read_csv(
                        filepath, delimiter="\t", low_memory=False
                    ).apply(pd.to_numeric, errors="coerce")
                    file[table_name] = df
        else:
            raise FileNotFoundError("Could not find the TAB files.")

        tmp_folder = self.folder_path / "tmp"
        if tmp_folder.exists():
            shutil.rmtree(tmp_folder)


RawLCFS = RawLCFS()
