from policyengine_core.data import Dataset
from policyengine_uk.data.storage import STORAGE_FOLDER
from pathlib import Path
import pandas as pd
import h5py


class RawSPI(Dataset):
    """A `Survey` instance for the Survey of Personal Incomes."""

    name = "raw_spi"
    label = "Survey of Personal Incomes"
    data_format = Dataset.TABLES
    tab_folder = None
    time_period = None
    
    def generate(self):
        if self.tab_folder is None:
            raise ValueError("`tab_folder` must be set to generate the dataset.")
    
        # Filename is tab/put1920.tab for 2019-20
        folder = Path(self.tab_folder) / "tab"
        two_digit_year = self.time_period % 100
        filename = f"put{two_digit_year:02d}{two_digit_year + 1:02d}uk.tab"
        file_path = folder / filename
        
        # Load the data
        main = pd.read_csv(file_path, sep="\t").fillna(0)
        main.to_hdf(STORAGE_FOLDER / "raw_spi_2019.h5", key="main", mode="w")

class RawSPI_2019(RawSPI):
    tab_folder = "~/Downloads/UKDA-9031-tab"
    time_period = 2019
    file_path = STORAGE_FOLDER / "raw_spi_2019.h5"
    label = "Raw SPI (2019-20)"
    name = "raw_spi_2019"