import pandas as pd


def project_psnd():
    from policyengine_uk_data.storage import STORAGE_FOLDER
    from policyengine_uk import Microsimulation

    OBR_PSND = [2_540, 2_691, 2_793, 2_820, 2_903, 2_995, 3_078]
    tax_ben = pd.read_csv(STORAGE_FOLDER / "tax_benefit.csv")
    REVENUES = [
        "income_tax",
        "ni_employee",
        "ni_employer",
        "vat",
        "fuel_duties",
        "tv_licence_fee",
    ]
    SPENDING = [
        "universal_credit",
        "tax_credits",
        "housing_benefit",
        "pip",
        "dla",
        "winter_fuel_allowance",
    ]
    tax_ben_revenues = (
        tax_ben[tax_ben.name.isin(REVENUES)].set_index("name").loc[REVENUES]
    )
    tax_ben_spending = (
        tax_ben[tax_ben.name.isin(SPENDING)].set_index("name").loc[SPENDING]
    )
    PE_REVENUES = [
        "income_tax",
        "ni_employee",
        "ni_employer",
        "vat",
        "fuel_duty",
        "tv_licence",
    ]
    PE_SPENDING = [
        "universal_credit",
        "tax_credits",
        "housing_benefit",
        "pip",
        "dla",
        "winter_fuel_allowance",
    ]
    baseline = Microsimulation()

    pe_psnd = []

    for year in range(2022, 2029):
        obr_psnd = OBR_PSND[year - 2022]
        obr_totals = (
            tax_ben_spending[str(year)].sum()
            - tax_ben_revenues[str(year)].sum()
        )
        pe_revenues = sum(
            baseline.calculate(variable, map_to="household", period=year).sum()
            / 1e9
            for variable in PE_REVENUES
        )
        pe_spending = sum(
            baseline.calculate(variable, map_to="household", period=year).sum()
            / 1e9
            for variable in PE_SPENDING
        )
        pe_totals = pe_spending - pe_revenues
        pe_psnd.append(obr_psnd + pe_totals - obr_totals)

    df = pd.DataFrame(
        {
            "year": range(2022, 2029),
            "OBR": OBR_PSND,
            "PE": pe_psnd,
        }
    )

    df["PE"] = df["PE"].round(1)

    df.to_csv("psnd.csv", index=False)


if __name__ == "__main__":
    project_psnd()
