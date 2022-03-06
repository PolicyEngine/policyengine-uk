import numpy as np
from openfisca_core.parameters import ParameterNode, Parameter
from numpy.typing import ArrayLike
from itertools import chain
from functools import reduce
from typing import Callable, Iterable, List, Tuple, Type
from openfisca_uk import Microsimulation
import tensorflow as tf


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
    if actual == 0:
        return tf.constant(0, dtype=tf.float32)
    return ((pred / actual) - 1) ** 2 * actual


def weighted_squared_log_relative_deviation(
    pred: tf.Tensor, actual: ArrayLike
) -> tf.Tensor:
    """Computes the squared log relative deviation between two tensors, weighted by the actual value.

    Args:
        pred (tf.Tensor): Predicted values.
        actual (ArrayLike): Actual values.

    Returns:
        tf.Tensor: The weighted squared log relative deviation.
    """
    if actual == 0:
        return tf.constant(0, dtype=tf.float32)
    return (tf.math.log(pred / actual) - 1) ** 2 * actual


class LossCategory:
    weight: float = 1
    label: str
    category: str
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
                    l = cls.comparison_loss_function(pred, actual)
                    log += [
                        dict(
                            name=name,
                            pred=float(pred.numpy()),
                            actual=float(actual),
                            loss=float(l.numpy()),
                            category=cls.category,
                        )
                    ]
                    loss += l
        if not validation and cls.initial_train_loss is None:
            cls.initial_train_loss = loss.numpy()
        elif validation and cls.initial_val_loss is None:
            cls.initial_val_loss = loss.numpy()
        initial_value = (
            cls.initial_val_loss if validation else cls.initial_train_loss
        ) / cls.weight
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


def combine_two_loss_categories(
    cls: Type[LossCategory],
    other_cls: Type[LossCategory],
    group_name: str = None,
) -> Type[LossCategory]:
    return type(
        f"{cls.__name__}+{other_cls.__name__}",
        (LossCategory,),
        {
            "weight": cls.weight + other_cls.weight,
            "label": f"{cls.label}+{other_cls.label}",
            "category": group_name or f"{cls.label}+{other_cls.label}",
            "get_loss_subcomponents": lambda sim, household_weights, year: chain(
                cls.get_loss_subcomponents(sim, household_weights, year),
                other_cls.get_loss_subcomponents(sim, household_weights, year),
            ),
            "get_metrics": lambda: chain(
                cls.get_metrics(), other_cls.get_metrics()
            ),
            "get_metric_names": lambda: chain(
                cls.get_metric_names(), other_cls.get_metric_names()
            ),
        },
    )


def combine_loss_categories(
    *loss_categories: Type[LossCategory], weight: float = 1, label: str = None
) -> Type[LossCategory]:
    category = reduce(
        lambda cat_1, cat_2: combine_two_loss_categories(
            cat_1, cat_2, group_name=label
        ),
        loss_categories,
    )
    category.weight = weight or category.weight
    return category
