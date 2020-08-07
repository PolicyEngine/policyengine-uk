from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_uk import CountryTaxBenefitSystem


TEST_CASE = {
    'persons': {
        'Matt': {
            'income': {'2016': 0}
        },
        'Jess': {
            'income': {'2016': 24000}
        },
        'Matthew': {
            'income': {'2016': 0}
        },
        'Jessica': {
            'income': {'2016': 24000}
        }
    },
    'marriages': {
        '1': {
            'partners': ['Matthew', 'Jessica']
        }
    }
}

tax_benefit_system = CountryTaxBenefitSystem()

simulation_builder = SimulationBuilder()
simulation = simulation_builder.build_from_entities(tax_benefit_system, TEST_CASE)
pre_tax_income = simulation.calculate('income', '2016')
post_tax_income_pp = simulation.calculate('basic_rate_tax', '2016')
post_tax_income_pm = simulation.calculate('marriage_post_tax_income', '2016')
print("person", simulation.persons.ids)
print("income", pre_tax_income)
print("post-tax income per person", post_tax_income_pp)
print("marriage", simulation.marriage.ids)
print("post-tax income per marriage", post_tax_income_pm)