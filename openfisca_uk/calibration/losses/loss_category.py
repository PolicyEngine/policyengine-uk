import tensorflow as tf
from openfisca_uk import Microsimulation
from typing import List, Tuple
from openfisca_core.parameters import ParameterNode, Parameter


class LossCategory:
    weight: float = 1
    label: str
    parameter_folder: ParameterNode
    years: List[int] = [2019, 2020, 2021, 2022]

    @classmethod
    def compute(
        cls,
        sim: Microsimulation,
        household_weights: tf.Tensor,
        year: int,
        excluded_metrics: List[str],
    ) -> Tuple[tf.Tensor, dict]:
        raise NotImplementedError()

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
