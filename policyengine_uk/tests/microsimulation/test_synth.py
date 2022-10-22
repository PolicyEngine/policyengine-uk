def test_synth_runs():
    from policyengine_uk import Microsimulation
    from policyengine_uk.data import SynthFRS

    if 2022 not in SynthFRS.years:
        SynthFRS.download(2022)

    sim = Microsimulation(dataset=SynthFRS)
    sim.calculate("household_net_income")
