from .universal_credit import UniversalCredit
from .pension_credit import PensionCredit
from ...loss_category import LossCategory

class Programs(LossCategory):
    name = "Programs"
    category = "Programs"

    def initialise(self):
        self.subcategories = []
        for subcategory in (UniversalCredit, PensionCredit):
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