

def test_pension_credit():
    from policyengine_uk import Microsimulation

    sim = Microsimulation(dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5")

    assert sim.calculate("pension_credit", 2025).sum() == 6486021485.618751