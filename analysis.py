import pandas
from openfisca_uk import CountryTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_uk.reforms.basic_income import bi_from_pa
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
bi_reformed_system = bi_from_pa(tax_benefit_system)
sb = SimulationBuilder()
sb.create_entities(bi_reformed_system)
sb.declare_person_entity('person', np.array(data['person_id']))
simulation_reformed = sb.build(bi_reformed_system)
for column in data.columns[1:]:
    simulation_reformed.set_input(column, period, np.array(data[column]))
data['net_income'] = simulation.calculate('net_income', period)
data['net_income_reformed'] = simulation_reformed.calculate('net_income', period)
sns.lineplot(data['earnings'] * 12, data['net_income'] * 12, ci=None)
sns.lineplot(data['earnings'] * 12, data['net_income_reformed'] * 12, ci=None, color='red')
plot = sns.lineplot(data['earnings'] * 12, data['net_income_reformed'] * 12 - data['net_income'] * 12, ci=None, color='grey')
plot.set(xlim=[0, 150000])
plot.set(ylim=[0, 150000])
plt.legend(labels=['baseline', 'reform', 'difference'])
plot.set_title('Change in net income with (+ UBI, - PA) reform')
plt.show()
