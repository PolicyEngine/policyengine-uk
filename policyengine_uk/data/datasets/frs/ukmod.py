import pandas as pd
from policyengine_uk.data.storage import STORAGE_FOLDER
import numpy as np
from policyengine_core.data import Dataset


class UKMOD_FRS_2018(Dataset):
    name = "ukmod_frs_2018"
    label = "UKMOD (2018-19 FRS)"
    data_format = Dataset.TIME_PERIOD_ARRAYS
    file_path = STORAGE_FOLDER / "ukmod_frs_2018.h5"
    time_period = "2018"

    def generate(self):
        data = {}
        ukmod_output = pd.read_csv(
            STORAGE_FOLDER / "uk_2018_std.txt", delimiter="\t"
        )
        ukmod_input = pd.read_csv(
            STORAGE_FOLDER / "uk_2018_a4.txt", delimiter="\t"
        )
        output_columns = [
            column
            for column in ukmod_output.columns
            if column not in ukmod_input.columns
        ]
        ukmod = pd.merge(
            ukmod_output[output_columns + ["idperson"]],
            ukmod_input,
            on="idperson",
            how="right",
        )
        # Add ID variables first
        data["person_id"] = ukmod.idperson
        data["person_benunit_id"] = person_benunit_id = (
            ukmod.idorigbenunit * 10 + ukmod.idorighh
        )
        data["person_household_id"] = person_household_id = (
            ukmod.idorighh * 100
        )
        data["person_state_id"] = np.ones_like(ukmod.idperson)

        data["benunit_id"] = person_benunit_id.unique()
        data["household_id"] = person_household_id.unique()
        data["state_id"] = np.array([1])

        data["age"] = ukmod.dag.values
        data["gender"] = np.where(
            ukmod.dgn == 0,
            "FEMALE",
            "MALE",
        ).astype("S")
        data["employment_income"] = ukmod.yem.values * 12
        data["self_employment_income"] = ukmod.yse.values * 12
        data["pension_income"] = ukmod.ypp.values * 12
        data["statutory_sick_pay"] = ukmod.bhlwk.values * 12
        data["statutory_maternity_pay"] = ukmod.bmact_s.values * 12
        data["statutory_paternity_pay"] = ukmod.bpact_s.values * 12

        for variable in data:
            data[variable] = {"2018": data[variable]}

        self.save_dataset(data)
