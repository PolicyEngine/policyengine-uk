from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk.parameters import parameters


class TenureType(LossCategory):
    weight = 1
    label = "Tenure type"
    parameter_folder = parameters.calibration.tenure_type

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        tenure_type = sim.calc("ons_tenure_type")
        hh_region = sim.calc("region")
        tenure_metrics = TenureType.parameter_folder
        for region in tenure_metrics.children:
            for tenure in tenure_metrics.children[region].children:
                parameter = tenure_metrics.children[region].children[tenure]
                parameter_name = parameter.name + "." + str(year)
                model_population = tf.reduce_sum(
                    (hh_region == region)
                    * (tenure_type == tenure)
                    * household_weights
                )
                actual_population = parameter(f"{year}-01-01")
                yield parameter_name, model_population, actual_population
