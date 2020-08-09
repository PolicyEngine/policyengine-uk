import pandas
from openfisca_uk import CountryTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

tax_benefit_system = CountryTaxBenefitSystem()
sb = SimulationBuilder()
sb.create_entities(tax_benefit_system)
data = pandas.read_csv('datasets/frs/frs.csv')
period = '2018-01'
sb.declare_person_entity('person', np.array(data['person_id']))
simulation = sb.build(tax_benefit_system)
for column in data.columns[1:]:
    simulation.set_input(column, period, np.array(data[column]))
data['net_income'] = simulation.calculate('net_income', period)
sns.scatterplot(data['earnings'], data['net_income'], ci=None, size=1)
plt.show()