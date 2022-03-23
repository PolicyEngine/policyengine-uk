from openfisca_uk import parameters


def add_takeup_parameters():
    """
    Calculate simulation-based benefit takeup parameters and prints them.
    """

    from openfisca_uk import Microsimulation

    years = list(range(2019, 2026))

    baseline = Microsimulation()
    full_benefit_claimants = Microsimulation()
    for year in years:
        full_benefit_claimants.set_input(
            "claims_all_entitled_benefits",
            year,
            [True] * len(baseline.calc("benunit_id", period=year)),
        )

    VARIABLES = [
        "universal_credit",
        "pension_credit",
        "working_tax_credit",
        "child_tax_credit",
        "income_support",
        "housing_benefit",
    ]

    takeup_parameters = [
        parameters.benefit.universal_credit.takeup,
        parameters.benefit.pension_credit.takeup,
        parameters.benefit.tax_credits.working_tax_credit.takeup,
        parameters.benefit.tax_credits.child_tax_credit.takeup,
        parameters.benefit.income_support.takeup,
        parameters.benefit.housing_benefit.takeup,
    ]

    for variable, parameter in zip(VARIABLES, takeup_parameters):
        parameter.values_list = []
        for year in years:
            baseline_claimants = (
                baseline.calc(variable, period=year) > 0
            ).sum()
            maximum_claimants = (
                full_benefit_claimants.calc(variable, period=year) > 0
            ).sum()
            parameter.update(
                value=round(baseline_claimants / maximum_claimants, 3),
                period=f"year:{year}:1",
            )
        print(f"{variable} benefit takeup parameter:\n\n{parameter}")


if __name__ == "__main__":
    add_takeup_parameters()
