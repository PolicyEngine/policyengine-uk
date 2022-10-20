from typing import Iterable

import numpy as np
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
    ESAIncome,
    JSAIncome,
    CouncilTax,
    TotalNI,
    EmploymentIncome,
    SelfEmploymentIncome,
    PensionIncome,
    SavingsInterestIncome,
    PropertyIncome,
    DividendIncome,
)
from .income_tax import IncomeTax


class Programs(LossCategory):
    name = "Programs"
    category = "Programs"
    weight = 2

    def initialise(self):
        self.initial_value = None
        self.subcategories = []
        for subcategory in (
            IncomeTax,
            UniversalCredit,
            ChildBenefit,
            ChildTaxCredit,
            WorkingTaxCredit,
            PensionCredit,
            IncomeSupport,
            StatePension,
            HousingBenefit,
            ESAIncome,
            JSAIncome,
            CouncilTax,
            TotalNI,
            EmploymentIncome,
            SelfEmploymentIncome,
            PensionIncome,
            SavingsInterestIncome,
            PropertyIncome,
            DividendIncome,
        ):
            self.subcategories.append(
                subcategory(
                    self.years,
                    self.year,
                    np.log(
                        self.sim.calc(
                            subcategory.variable, period=self.year
                        ).sum()
                        + np.e
                    ),
                    self.sim,
                )
            )

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
