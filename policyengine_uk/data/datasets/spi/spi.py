from policyengine_core.data import Dataset
from typing import Type
from pathlib import Path
import numpy as np
from .raw_spi import RawSPI_2019
from policyengine_uk.data.storage import STORAGE_FOLDER


class SPI(Dataset):
    raw_spi: Type[Dataset]
    time_period: int
    label: str
    name: str
    data_format: str = Dataset.TIME_PERIOD_ARRAYS
    file_path: Path

    def generate(self):
        main = self.raw_spi().load("main")
        person_id = benunit_id = household_id = main.SREF
        data = {
            "person_id": person_id,
            "benunit_id": benunit_id,
            "household_id": household_id,
            "state_id": np.ones_like(person_id),
        }
        data["person_state_id"] = data["state_id"][...]
        data["person_benunit_id"] = data["benunit_id"][...]
        data["person_household_id"] = data["household_id"][...]

        data["employment_income"] = (
            np.maximum(0, main.PAY + main.EPB - main.EXPS)
            + main.INCPBEN
            + main.OSSBEN
            + main.TAXTERM
            + main.UBISJA
            + main.MOTHINC
        )
        data["household_weight"] = main.FACT

        for variable in data:
            data[variable] = {self.time_period: np.array(data[variable])}

        self.save_dataset(data)


class SPI_2019(SPI):
    raw_spi = RawSPI_2019
    time_period = 2019
    file_path = STORAGE_FOLDER / "spi_2019.h5"
    name = "spi_2019"
    label = "SPI (2019-20)"
