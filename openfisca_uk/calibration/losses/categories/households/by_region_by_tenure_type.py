from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import parameters


class HouseholdsByRegionByTenureType(LossCategory):
    label = "Households by region and tenure type"
    parameter_folder = (
        parameters.calibration.households.by_region_by_tenure_type
    )
    weight = 1 / 30

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        total_households = parameters.calibration.households.in_total(
            f"{year}-01-01"
        )
        total_tenure_metrics = sum(
            [
                parameter(f"{year}-01-01")
                for parameter in HouseholdsByRegionByTenureType.get_metrics()
            ]
        )
        adjustment = total_households / total_tenure_metrics
        tenure_type = sim.calc("ons_tenure_type").values
        hh_country = sim.calc("country").values
        tenure_metrics = HouseholdsByRegionByTenureType.parameter_folder
        for country in tenure_metrics.children:
            for tenure in tenure_metrics.children[country].children:
                parameter = tenure_metrics.children[country].children[tenure]
                parameter_name = parameter.name + "." + str(year)
                model_population = tf.reduce_sum(
                    (hh_country == country)
                    * (tenure_type == tenure)
                    * household_weights
                )
                actual_population = parameter(f"{year}-01-01") * adjustment
                yield parameter_name, model_population, actual_population
