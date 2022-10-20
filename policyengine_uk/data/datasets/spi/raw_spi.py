import shutil
from openfisca_tools.data import PrivateDataset
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from openfisca_uk.data.storage import OPENFISCA_UK_MICRODATA_FOLDER


class RawSPI(PrivateDataset):
    name = "raw_spi"
    label = "Raw SPI"
    folder_path = OPENFISCA_UK_MICRODATA_FOLDER
    is_openfisca_compatible = False

    filename_by_year = {
        2018: "raw_spi_2018.h5",
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
            raise FileNotFoundError("Invalid path supplied")
        new_folder = self.folder_path / "tmp"
        shutil.unpack_archive(folder, new_folder)
        folder = new_folder
        main_folder = next(folder.iterdir())
        with pd.HDFStore(RawSPI.file(year)) as file:
            if (main_folder / "tab").exists():
                data_folder = main_folder / "tab"
                data_files = list(data_folder.glob("*.tab"))
                task = tqdm(data_files, desc="Saving data tables")
                for filepath in task:
                    task.set_description(f"Saving {filepath.name}")
                    table_name = "main"
                    df = pd.read_csv(
                        filepath, delimiter="\t", low_memory=False
                    ).apply(pd.to_numeric, errors="coerce")
                    df.columns = df.columns.str.upper()
                    file[table_name] = df
            else:
                raise FileNotFoundError("Could not find any TAB files.")

        # Clean up tmp storage.

        tmp_folder = self.folder_path / "tmp"
        if tmp_folder.exists():
            shutil.rmtree(tmp_folder)


RawSPI = RawSPI()
