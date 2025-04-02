

def test_hnet():
    from policyengine_uk import Microsimulation

    sim = Microsimulation(dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5")

    assert sim.calculate("household_net_income", 2025).sum() == 1597226815671.2178