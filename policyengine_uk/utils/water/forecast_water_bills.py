import pandas as pd
from pathlib import Path
from microdf import MicroDataFrame


def project_water_bills():
    df_pre_2025 = pd.DataFrame(
        {
            "Year": [2021, 2022, 2023, 2024, 2025],
            "Oftwat avg bills (real)": [486, 470, 486, 492, 503],
            "CPIH": [113.1, 123.0, 129.9, 134.0, 139.0],
        }
    )

    df_pre_2025["Oftwat avg bills (nominal)"] = (
        df_pre_2025["Oftwat avg bills (real)"] * df_pre_2025["CPIH"] / 100
    )
    df_pre_2025["Oftwat avg bills (nominal)"] = (
        df_pre_2025["Oftwat avg bills (nominal)"]
        / df_pre_2025["Oftwat avg bills (nominal)"].iloc[0]
        * 100
    ).round(1)
    df_pre_2025["Nominal YoY change"] = (
        df_pre_2025["Oftwat avg bills (nominal)"].pct_change() * 100
    ).round(1)

    proposed_increases = pd.read_csv(
        Path(__file__).parent / "ofwat_increases.csv"
    )
    proposed_increases = MicroDataFrame(
        proposed_increases, weights="Customers"
    )
    avg_bills_2025_onwards = (
        proposed_increases[proposed_increases.columns[2:]].mean().values
    )

    df_post_2025 = pd.DataFrame(
        {
            "Year": [2024, 2025, 2026, 2027, 2028, 2029],
            "CPIH": [134.0, 139.0, 142.2, 145.2, 148.2, 151.3],
            "Pre-inflation avg bills (nominal)": avg_bills_2025_onwards,
        }
    )

    # Add CPIH to each year's change

    df_post_2025["Avg bills (nominal)"] = df_post_2025[
        "Pre-inflation avg bills (nominal)"
    ].values
    df_post_2025["CPIH change"] = df_post_2025["CPIH"].pct_change() * 100

    for year in range(2025, 2030):
        row = df_post_2025[df_post_2025["Year"] == year].iloc[0]
        cpi_change = (
            row["CPIH"]
            / df_post_2025[df_post_2025["Year"] == year - 1]["CPIH"].values[0]
            - 1
        ) * 100
        # Increase the nominal bills by the CPIH change
        addition = df_post_2025.loc[
            df_post_2025["Year"] == year - 1, "Avg bills (nominal)"
        ].values[0] * (cpi_change / 100)
        # Add addition to this and future years
        df_post_2025.loc[
            df_post_2025["Year"] >= year, "Avg bills (nominal)"
        ] += addition

    df_post_2025["Relative change"] = (
        df_post_2025["Avg bills (nominal)"].pct_change() * 100
    ).round(1)

    df_post_2025.to_csv("test.csv")

    df_post_2025

    combined_water_forecast = pd.DataFrame(
        {
            "Year": list(range(2022, 2030)),
            "Average nominal bills YoY change": df_pre_2025[
                "Nominal YoY change"
            ].tolist()[1:-1]
            + df_post_2025["Relative change"].tolist()[1:],
        }
    )

    print(combined_water_forecast.to_markdown(index=False))


if __name__ == "__main__":
    project_water_bills()
