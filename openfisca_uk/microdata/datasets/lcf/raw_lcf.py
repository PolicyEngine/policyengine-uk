from pathlib import Path
from openfisca_uk.microdata.utils import dataset
import pandas as pd
import shutil
from openfisca_uk.microdata.utils import safe_rmdir
import re
from tqdm import tqdm


@dataset
class RawLCF:
    name = "raw_lcf"

    def generate(zipfile, year) -> None:
        folder = Path(zipfile)
        year = str(year)

        if not folder.exists():
            raise FileNotFoundError("Invalid path supplied.")

        new_folder = RawLCF.data_dir / "tmp"
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
            with pd.HDFStore(RawLCF.file(year)) as file:
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

        tmp_folder = RawLCF.data_dir / "tmp"
        if tmp_folder.exists():
            safe_rmdir(tmp_folder)
