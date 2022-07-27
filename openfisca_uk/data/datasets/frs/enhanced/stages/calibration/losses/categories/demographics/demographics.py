from typing import Iterable
from .households import Households
from .populations import Populations
from ...loss_category import LossCategory


class Demographics(LossCategory):
    name = "Demographics"
    category = "Demographics"
    weight = 1

    def initialise(self):
        self.initial_value = None
        self.subcategories = [
            Households(self.years, self.year, 1, self.sim),
            Populations(self.years, self.year, 1, self.sim),
        ]

    def compute(self, *args, **kwargs):
        losses = 0
        log = []
        for subcategory in self.subcategories:
            additional_loss, additional_log = subcategory.compute(
                *args, **kwargs
            )
            losses += additional_loss * self.weight
            log += additional_log
        if self.initial_value is None:
            self.initial_value = losses
        losses /= self.initial_value
        for entry in log:
            entry["loss"] /= self.initial_value
        return losses, log

    def get_metric_names(self) -> Iterable[str]:
        names = sum(
            [
                subcategory.get_metric_names()
                for subcategory in self.subcategories
            ],
            [],
        )
        dated_names = []
        for name in names:
            for year in self.years:
                dated_names.append(f"{name}.{year}")
        return dated_names
