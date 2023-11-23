import pandas as pd
from pathlib import Path

lha_list_of_rents = pd.read_csv(
    Path(__file__).parent / "local_housing_allowance_list_of_rents.csv.gz",
    compression="gzip",
)
