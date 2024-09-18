import pandas as pd
from pathlib import Path

lha_list_of_rents = pd.read_csv(
    Path(__file__).parent / "lha_list_of_rents.csv.gz"
)
