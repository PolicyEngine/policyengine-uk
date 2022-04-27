from ...loss_category import LossCategory

class IncomeTax(LossCategory):
    name = "Income Tax"
    category = "Programs"

    def initialise(self):
        values = sim.calc("income_tax", period=self.year)