import pandas as pd
from pathlib import Path

FOLDER = Path(__file__).parent

lha_list_of_rents = pd.read_csv(
    FOLDER / "local_housing_allowance_list_of_rents.csv.gz",
    compression="gzip",
)

brma_to_region = pd.read_csv(
    FOLDER / "brma_to_region.csv.gz", compression="gzip"
)

enhanced_frs_brmas = pd.read_csv(
    FOLDER / "enhanced_frs_brmas.csv.gz", compression="gzip"
)
