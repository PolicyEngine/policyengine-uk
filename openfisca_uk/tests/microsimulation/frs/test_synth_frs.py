def test_synth_downloads():
    from openfisca_uk.microdata import SynthFRS

    SynthFRS.download(2018)
    SynthFRS.download(2019)
    assert SynthFRS.file(2018).exists()
    assert SynthFRS.file(2019).exists()


def test_synth_works_with_openfisca_uk():
    from openfisca_uk import Microsimulation
    from openfisca_uk.microdata import SynthFRS

    sim = Microsimulation(
        dataset=SynthFRS,
        year=2019,
    )
    assert not sim.calc("net_income", 2022).isna().any()
