from pathlib import Path

import pandas as pd

lha_list_of_rents = pd.read_csv(Path(__file__).parent / "lha_list_of_rents.csv.gz")
