import logging
from policyengine_core.data import PrivateDataset, Dataset
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER
from ..extension import ExtendedFRS
import h5py


class CalibratedFRS(PrivateDataset):
    name = "calibrated_frs"
    label = "Calibrated FRS"
    data_format = Dataset.TIME_PERIOD_ARRAYS

    folder_path = policyengine_uk_MICRODATA_FOLDER

    def generate(self, year: int):
        if year not in ExtendedFRS.years:
            ok = input(
                f"Extended FRS not found for year {year}. Generate it? (y/n)"
            )
            if ok == "y":
                ExtendedFRS.generate(year)

        # Copy all data from the extended FRS

        extended_frs = ExtendedFRS.load(year)
        calibrated_frs = h5py.File(self.file(year), mode="w")
        for variable in extended_frs.keys():
            for period in extended_frs[variable].keys():
                calibrated_frs[f"{variable}/{period}"] = extended_frs[
                    variable
                ][period][...]
        extended_frs.close()
        calibrated_frs.close()

        from .calibrate import HouseholdWeights

        weights = HouseholdWeights(
            start_year=2022,
            end_year=2027,
        )
        weights.calibrate(
            validation_split=0,
            num_epochs=1024,
            learning_rate=1e3,
            dataset=self,
        )

        weights.save()


CalibratedFRS = CalibratedFRS()
