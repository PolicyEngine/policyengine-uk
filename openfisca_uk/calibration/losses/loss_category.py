import tensorflow as tf
from openfisca_uk import Microsimulation
from typing import Callable, Iterable, List, Tuple
from numpy.typing import ArrayLike
from openfisca_core.parameters import ParameterNode, Parameter


def weighted_squared_relative_deviation(
    pred: tf.Tensor, actual: ArrayLike
) -> tf.Tensor:
    if actual == 0:
        return tf.constant(0, dtype=tf.float32)
    return ((pred / actual) - 1) ** 2 * actual


class LossCategory:
    weight: float = 1
    label: str
    parameter_folder: ParameterNode
    years: List[int] = [2019, 2020, 2021, 2022]
    comparison_loss_function: Callable = weighted_squared_relative_deviation
    initial_train_loss: float = None
    initial_val_loss: float = None

    def get_loss_subcomponents(
        sim: Microsimulation, household_weights: tf.Tensor, year: int
    ) -> Iterable[Tuple]:
        """Gathers predictions used to measure weight performance.

        Args:
            sim (Microsimulation): A microsimulation from which to draw demographic data.
            household_weights (tf.Tensor): Household weights for each year.
            year (int): The year to test on.

        Returns:
            Iterable[Tuple]: A list of (name, pred, actual) triplets.
        """
        raise NotImplementedError()

    @classmethod
    def compute(
        cls,
        sim: Microsimulation,
        household_weights: tf.Tensor,
        excluded_metrics: List[str],
        validation: bool = False,
    ) -> Tuple[tf.Tensor, dict]:
        loss = tf.constant(0, dtype=tf.float32)
        log = []
        for year in cls.years:
            for name, pred, actual in cls.get_loss_subcomponents(
                sim, household_weights[year - cls.years[0]], year
            ):
                if name not in excluded_metrics:
                    l = cls.comparison_loss_function(pred, actual) * cls.weight
                    log += [
                        dict(
                            name=name,
                            pred=float(pred.numpy()),
                            actual=float(actual),
                            loss=float(l.numpy()),
                            category=cls.label,
                        )
                    ]
                    loss += l
        if not validation and cls.initial_train_loss is None:
            cls.initial_train_loss = loss.numpy()
        elif validation and cls.initial_val_loss is None:
            cls.initial_val_loss = loss.numpy()
        initial_value = (
            cls.initial_val_loss if validation else cls.initial_train_loss
        )
        if initial_value == 0:
            initial_value += 1
        for entry in log:
            entry["loss"] /= initial_value
        if len(log) == 0:
            return loss, log
        return loss / initial_value, log

    @classmethod
    def get_metrics(cls) -> List[Parameter]:
        return list(
            filter(
                lambda p: isinstance(p, Parameter),
                cls.parameter_folder.get_descendants(),
            )
        )

    @classmethod
    def get_metric_names(cls) -> List[str]:
        for parameter in cls.parameter_folder.get_descendants():
            if isinstance(parameter, Parameter):
                yield from [f"{parameter.name}.{year}" for year in cls.years]
