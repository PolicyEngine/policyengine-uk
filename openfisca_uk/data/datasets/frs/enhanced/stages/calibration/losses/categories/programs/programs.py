from typing import Iterable
from ...loss_category import LossCategory
from .country_level_program import (
    UniversalCredit,
    ChildBenefit,
    ChildTaxCredit,
    WorkingTaxCredit,
    PensionCredit,
    IncomeSupport,
    StatePension,
    HousingBenefit,
    ESA_income,
    JSA_income,
    CouncilTax,
    TotalNI,
)

class Programs(LossCategory):
    name = "Programs"
    category = "Programs"

    def initialise(self):
        self.subcategories = []
        for subcategory in (
                UniversalCredit,
                ChildBenefit,
                ChildTaxCredit,
                WorkingTaxCredit,
                PensionCredit,
                IncomeSupport,
                StatePension,
                HousingBenefit,
                ESA_income,
                JSA_income,
                CouncilTax,
                TotalNI,
            ):
            self.subcategories.append(subcategory(
                self.years, 
                self.year,
                self.sim.calc(subcategory.variable, period=self.year).sum()/1e11,
                self.sim,
            ))
    
    def compute(self, *args, **kwargs):
        losses = 0
        log = []
        for subcategory in self.subcategories:
            additional_loss, additional_log = subcategory.compute(*args, **kwargs)
            losses += additional_loss
            log += additional_log
        return losses, log
    
    def get_metric_names(self) -> Iterable[str]:
        return sum([subcategory.get_metric_names() for subcategory in self.subcategories], [])