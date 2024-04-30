from policyengine_core.data import Dataset
from pathlib import Path
import numpy as np
from typing import Type
from ..utils import STORAGE_FOLDER
from .frs import FRS_2019_20
from .calibration.calibrated_frs import CalibratedSPIEnhancedPooledFRS_2019_21
import yaml
import copy


class ImputationExtendedFRS(Dataset):
    name = "imputation_extended_frs"
    label = "Imputation-extended FRS"
    file_path = STORAGE_FOLDER / "imputation_extended_frs.h5"
    data_format = Dataset.TIME_PERIOD_ARRAYS
    input_dataset = None
    num_years = 1

    @staticmethod
    def from_dataset(
        dataset: Type[Dataset],
        new_name: str = "imputation_extended_frs",
        new_label: str = "Imputation-extended FRS",
        new_url: str = None,
        new_time_period: int = None,
        new_num_years: int = 1,
    ):
        class ImputationExtendedFRSFromDataset(ImputationExtendedFRS):
            name = new_name
            label = new_label
            input_dataset = dataset
            file_path = STORAGE_FOLDER / f"{new_name}.h5"
            time_period = new_time_period or dataset.time_period
            data_format = Dataset.TIME_PERIOD_ARRAYS
            url = new_url
            num_years = new_num_years

        return ImputationExtendedFRSFromDataset

    def generate(self):
        from policyengine_uk import Microsimulation
        from survey_enhance import Imputation

        simulation = Microsimulation(dataset=self.input_dataset)

        data = self.input_dataset().load_dataset()

        # We're imputing consumption, wealth and VAT.

        IMPUTATIONS = STORAGE_FOLDER / "imputations"

        consumption = Imputation.load(IMPUTATIONS / "consumption.pkl")
        wealth = Imputation.load(IMPUTATIONS / "wealth.pkl")
        vat = Imputation.load(IMPUTATIONS / "vat.pkl")

        # Target aggregates for wealth and consumption variables
        with open(IMPUTATIONS / "wealth_targets.yaml") as f:
            wealth_targets = yaml.load(f, Loader=yaml.FullLoader)

        with open(IMPUTATIONS / "consumption_targets.yaml") as f:
            consumption_targets = yaml.load(f, Loader=yaml.FullLoader)

        i = 0
        frs_household_weight = simulation.calculate("household_weight").values
        for imputation_model, targets in zip(
            [consumption, vat, wealth],
            [{}, {}, {}],
        ):
            i += 1
            predictors = imputation_model.X_columns

            X_input = simulation.calculate_dataframe(
                predictors, map_to="household"
            )
            if i == 3:
                # WAS doesn't sample NI -> put NI households in Wales (closest aggregate)
                X_input.loc[
                    X_input["region"] == "NORTHERN_IRELAND", "region"
                ] = "WALES"
            if len(targets) > 0:
                target_values = [
                    targets[output] for output in imputation_model.Y_columns
                ]
                quantiles = imputation_model.solve_for_mean_quantiles(
                    target_values,
                    X_input,
                    frs_household_weight,
                    max_iterations=3,
                )
            else:
                quantiles = None
            Y_output = imputation_model.predict(
                X_input, mean_quantile=quantiles, verbose=True
            )

            for output_variable in Y_output.columns:
                values = Y_output[output_variable].values
                data[output_variable] = {self.time_period: values}

        from policyengine_uk.tools.drop_zero_weight_households import (
            drop_zero_weight_households,
        )
        from policyengine_uk.tools.stack_datasets import stack_datasets
        from policyengine_uk.data.datasets.frs.imputations.capital_gains import (
            impute_capital_gains,
        )

        self.save_dataset(data)

        drop_zero_weight_households(self)

        data = self.load_dataset()

        zero_weight_copy_1 = copy.deepcopy(data)
        zero_weight_copy_2 = copy.deepcopy(data)

        for time_period in zero_weight_copy_2["household_weight"]:
            zero_weight_copy_2["household_weight"][time_period] = (
                np.zeros_like(
                    zero_weight_copy_1["household_weight"][time_period]
                )
            )

        data = stack_datasets(data, zero_weight_copy_2)

        self.save_dataset(data)

        pred_cg, household_weights_21 = impute_capital_gains(2021)

        data["capital_gains"] = {2021: pred_cg}
        data["household_weight"][2021] = household_weights_21

        for year in range(2022, 2028):
            _, data["household_weight"][year] = impute_capital_gains(year)

        self.save_dataset(data)


EnhancedFRS = ImputationExtendedFRS.from_dataset(
    CalibratedSPIEnhancedPooledFRS_2019_21,
    "enhanced_frs",
    "Enhanced FRS",
    new_num_years=7,
    new_url="release://policyengine/non-public-microdata/uk-2024-march-efo/enhanced_frs.h5",
)
