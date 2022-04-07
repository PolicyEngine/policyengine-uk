from openfisca_uk.microdata.utils import *
from pathlib import Path
import shutil
from tqdm import tqdm
import pandas as pd


@dataset
class RawSPI:
    name = "raw_spi"

    def generate(zipfile, year) -> None:
        folder = Path(zipfile)
        year = str(year)
        if not folder.exists():
            raise FileNotFoundError("Invalid path supplied")
        new_folder = RawSPI.data_dir / "tmp"
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

        tmp_folder = RawSPI.data_dir / "tmp"
        if tmp_folder.exists():
            shutil.rmtree(tmp_folder)
