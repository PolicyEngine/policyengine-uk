def test_synth_runs():
    from policyengine_uk import Microsimulation
    from policyengine_uk.data import SynthFRS

    sim = Microsimulation(dataset=SynthFRS)
    sim.calc("net_income")
