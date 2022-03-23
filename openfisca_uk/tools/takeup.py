

def add_takeup_parameters():
    """
    Calculate simulation-based benefit takeup parameters and add them to the parameter tree folder in the repo.
    """

    from openfisca_uk import Microsimulation

    years = list(range(2019, 2026))

    baseline = Microsimulation()
    full_benefit_claimants = Microsimulation()
    for year in years:
        full_benefit_claimants.set_input("claims_all_entitled_benefits", year, [True] * len(baseline.calc("benunit_id", period=year)))