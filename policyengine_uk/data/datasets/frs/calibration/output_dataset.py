from policyengine_core.data import Dataset
from typing import Type
import pandas as pd
from pathlib import Path
from ...utils import STORAGE_FOLDER


class OutputDataset(Dataset):
    data_format = Dataset.TABLES
    input_dataset: Type[Dataset]
    time_period: int

    @staticmethod
    def from_dataset(dataset: Type[Dataset], new_time_period: int = None):
        class OutputDatasetFromDataset(OutputDataset):
            name = f"{dataset.name}"
            label = f"{dataset.label}"
            input_dataset = dataset
            time_period = new_time_period
            file_path = STORAGE_FOLDER / f"output_{dataset.name}.h5"

        return OutputDatasetFromDataset

    def generate(self):
        from policyengine_uk import Microsimulation

        sim = Microsimulation(dataset=self.input_dataset)

        PERSON_VARIABLES = [
            "age",
            "gender",
            "region",
            "country",
            "person_id",
            "tax_band",
            "adjusted_net_income",
        ]

        HOUSEHOLD_VARIABLES = [
            "household_id",
            "region",
            "country",
            "ons_tenure_type",
            "council_tax_band",
            "household_weight",
            "uc_child_limit_affected",
            "ctc_child_limit_affected",
            "is_child",
        ]

        PROGRAM_VARIABLES = [
            "income_support",
            "pension_credit",
            "working_tax_credit",
            "child_benefit",
            "child_tax_credit",
            "universal_credit",
            "state_pension",
            "total_NI",
            "JSA_income",
            "housing_benefit",
            "ESA_income",
            "employment_income",
            "self_employment_income",
            "pension_income",
            "property_income",
            "savings_interest_income",
            "council_tax_less_benefit",
            "dividend_income",
            "income_tax",
        ]

        variables = sim.tax_benefit_system.variables

        person = pd.DataFrame()

        for variable in PERSON_VARIABLES:
            person[variable] = sim.calculate(
                variable, map_to="person", period=self.time_period
            ).values

        household = pd.DataFrame()

        for variable in HOUSEHOLD_VARIABLES:
            household[variable] = sim.calculate(
                variable, period=self.time_period, map_to="household"
            ).values

        for variable in PROGRAM_VARIABLES:
            if variables[variable].entity.key != "household":
                person[variable] = sim.calculate(
                    variable, map_to="person", period=self.time_period
                ).values
                household[variable] = sim.calculate(
                    variable, map_to="household", period=self.time_period
                ).values
                household[f"{variable}_participants"] = sim.map_result(
                    sim.calculate(variable, period=self.time_period).values
                    > 0,
                    variables[variable].entity.key,
                    "household",
                )
            else:
                household[variable] = sim.calculate(
                    variable, period=self.time_period
                ).values

        person["person_household_id"] = sim.calculate(
            "household_id", map_to="person", period=self.time_period
        ).values

        self.save_dataset(
            dict(
                person=person,
                household=household,
            )
        )
