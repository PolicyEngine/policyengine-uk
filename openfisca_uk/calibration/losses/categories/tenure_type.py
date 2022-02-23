from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk.parameters import parameters


class TenureType(LossCategory):
    weight = 1e3
    label = "Tenure type"
    parameter_folder = parameters.calibration.tenure_type

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        tenure_type = sim.calc("ons_tenure_type")
        hh_country = sim.calc("country")
        tenure_metrics = TenureType.parameter_folder
        for country in tenure_metrics.children:
            for tenure in tenure_metrics.children[country].children:
                parameter = tenure_metrics.children[country].children[tenure]
                parameter_name = parameter.name + "." + str(year)
                model_population = tf.reduce_sum(
                    (hh_country == country)
                    * (tenure_type == tenure)
                    * household_weights
                )
                actual_population = parameter(f"{year}-01-01")
                yield parameter_name, model_population, actual_population
