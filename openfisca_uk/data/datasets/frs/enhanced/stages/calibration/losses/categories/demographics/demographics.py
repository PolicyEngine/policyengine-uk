from typing import Iterable
from .households import Households
from .populations import Populations
from ...loss_category import LossCategory


class Demographics(LossCategory):
    name = "Demographics"
    category = "Demographics"

    def initialise(self):
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
            losses += additional_loss
            log += additional_log
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
