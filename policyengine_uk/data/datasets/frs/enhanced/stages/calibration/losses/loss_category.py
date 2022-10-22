import numpy as np
from policyengine_core.parameters import ParameterNode, Parameter
from numpy.typing import ArrayLike
from itertools import chain
from functools import reduce
from typing import Callable, Iterable, List, Tuple, Type
from policyengine_uk import Microsimulation
from policyengine_uk.parameter_tree import parameters
import tensorflow as tf


@staticmethod
def weighted_squared_relative_deviation(
    pred: tf.Tensor, actual: ArrayLike
) -> tf.Tensor:
    """Computes the squared relative deviation between two tensors, weighted by the actual value.

    Args:
        pred (tf.Tensor): Predicted values.
        actual (ArrayLike): Actual values.

    Returns:
        tf.Tensor: The weighted squared relative deviation.
    """
    return (pred / (actual + 1) - 1) ** 2


class LossCategory:
    weight: float = 1
    label: str
    category: str
    parameter_folder: ParameterNode
    comparison_loss_function: Callable = weighted_squared_relative_deviation
    initial_train_loss: float = None
    initial_val_loss: float = None
    cache = {}
    use_cache = False

    def __init__(
        self, years: List[int], year: int, weight: float, sim: Microsimulation
    ):
        self.years = years or self.years
        self.year = year
        self.weight = weight
        self.sim = sim
        self.calibration_parameters = parameters.calibration(
            f"{self.year}-01-01"
        )
        self.initialise()

    def initialise(self):
        pass

    def get_loss_subcomponents(
        household_weights: tf.Tensor,
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

    def compute(
        self,
        sim: Microsimulation,
        household_weights: tf.Tensor,
        excluded_metrics: List[str],
        validation: bool = False,
    ) -> Tuple[tf.Tensor, dict]:
        loss = tf.constant(0, dtype=tf.float32)
        log = []
        for name, pred, actual in self.get_loss_subcomponents(
            household_weights[self.year - self.years[0]],
        ):
            name += f".{self.year}"
            if name not in excluded_metrics:
                l = self.comparison_loss_function(pred, actual)
                log += [
                    dict(
                        name=name,
                        pred=float(pred.numpy()),
                        actual=float(actual),
                        loss=float(l.numpy()),
                        category=self.category,
                    )
                ]
                loss += l
        if not validation and self.initial_train_loss is None:
            self.initial_train_loss = loss.numpy()
        elif validation and self.initial_val_loss is None:
            self.initial_val_loss = loss.numpy()
        initial_value = (
            self.initial_val_loss if validation else self.initial_train_loss
        )
        if initial_value == 0:
            initial_value += 1
        for entry in log:
            entry["loss"] /= initial_value
            entry["loss"] *= self.weight
        if len(log) == 0:
            return loss, log
        return loss / initial_value * self.weight, log

    def get_metrics(self) -> List[Parameter]:
        return []
        return list(
            filter(
                lambda p: isinstance(p, Parameter),
                self.parameter_folder.get_descendants(),
            )
        )

    def get_metric_names(self) -> List[str]:
        return []
        for parameter in self.parameter_folder.get_descendants():
            if isinstance(parameter, Parameter):
                yield f"{parameter.name}.{self.year}"
