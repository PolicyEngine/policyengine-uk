import pandas as pd
from pathlib import Path


def __getattr__(name):
    # The list of rents is large, and only percentile reforms need it, so it
    # is read on first access rather than when the package is imported.
    if name == "lha_list_of_rents":
        return pd.read_csv(Path(__file__).parent / "lha_list_of_rents.csv.gz")
    raise AttributeError(name)
