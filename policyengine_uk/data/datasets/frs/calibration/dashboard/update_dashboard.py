from policyengine_uk.data.datasets.frs.calibration.loss import get_snapshot
from policyengine_uk.data.storage import STORAGE_FOLDER
import pandas as pd


def main():
    YEARS = ["2024"]#, "2025", "2026", "2027", "2028"]
    DATASETS = ["frs_2021", "enhanced_frs"]

    dfs = []

    for year in YEARS:
        for dataset in DATASETS:
            print(dataset, year)
            df = get_snapshot(dataset, year)
            df["time_period"] = year
            df["dataset"] = dataset
            dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    df.to_csv(
        STORAGE_FOLDER / "dataset_losses.csv.gz",
        index=False,
        compression="gzip",
    )


if __name__ == "__main__":
    main()
