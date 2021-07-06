from openfisca_uk.api import Microsimulation

def test_household_net_income():
    sim = Microsimulation()
    assert ~sim.calc("household_net_income", map_to="person").isna().any()