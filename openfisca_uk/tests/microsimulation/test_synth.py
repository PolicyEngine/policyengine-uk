def test_synth_runs():
    from openfisca_uk import Microsimulation
    from openfisca_uk_data import SynthFRS

    sim = Microsimulation(dataset=SynthFRS)
    sim.calc("net_income")
