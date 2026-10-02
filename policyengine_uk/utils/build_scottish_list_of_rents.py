"""Put Scotland's own lists of rents into ``lha_list_of_rents.csv.gz``.

The Scottish rows that came with the file were copies of English BRMAs' lists.
The Scottish Government released Rent Service Scotland's market evidence, one
row per rent, under FOI 202200303624. Each worksheet holds the rents collected
in the twelve months to September of its year, which set the next April's
determination, so sheet ``Y - 1`` is the list for April ``Y``. This replaces the
Scottish rows for 2019 and 2020 with sheets 2018 and 2019, keeping only each
rent, its BRMA and its LHA category, and leaves every other row as it was.

Spreadsheet readers are not runtime dependencies, so run the build with them:

    uv run --with openpyxl python scripts/build_scottish_list_of_rents.py \
        --cache ~/.cache/lha
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from policyengine_uk.utils.build_lha_published_rates import fetch, scottish_brma
from policyengine_uk.utils.lha import CATEGORIES, LIST_OF_RENTS_PATH

SOURCE = pd.Series(
    {
        "id": "scot-foi-202200303624-brma-2016-2021",
        "file": "FOI-202200303624-Information-Released-BRMA-2016-2021.xlsx",
        "url": (
            "https://www.gov.scot/binaries/content/documents/govscot/publications/"
            "foi-eir-release/2023/08/foi-202200303624/documents/"
            "foi-202200303624---information-released---brma-2016-2021/"
            "foi-202200303624---information-released---brma-2016-2021/"
            "govscot%3Adocument/FOI%2B202200303624%2B-%2BInformation%2BReleased"
            "%2B-%2BBRMA%2B2016-2021.xlsx?download=true"
        ),
        "landing_page": "https://www.gov.scot/publications/foi-202200303624/",
        "sha256": "dba86fa1cce920c8f646460bb13e1d99e16927d57fdf290e874f9631e804ed06",
    }
)
YEARS = (2019, 2020)  # April determinations; sheet = year - 1.


def scottish_lists(path: Path) -> pd.DataFrame:
    frames = []
    for year in YEARS:
        sheet = pd.read_excel(path, sheet_name=str(year - 1)).dropna(how="all")
        # Sheet 2019 ends with two rents that name no BRMA; they cannot be placed.
        assert sheet["BRMA"].isna().sum() <= 2
        sheet = sheet[sheet["BRMA"].notna()]
        assert (sheet["FREQUENCY"] == "Weekly").all()
        assert (
            sheet["YEAR ENDING SEPTEMBER"] == f"{year - 2}/{str(year - 1)[2:]}"
        ).all()
        category = sheet["LHA TYPE"].str.strip().str.removeprefix("Cat ")
        assert category.isin(CATEGORIES).all()
        frames.append(
            pd.DataFrame(
                {
                    "weekly_rent": sheet["NET RENT"].astype(float).round(2),
                    "year": year,
                    "brma": sheet["BRMA"].map(scottish_brma),
                    "lha_category": category,
                    "region": "SCOTLAND",
                }
            )
        )
    lists = pd.concat(frames, ignore_index=True)
    return lists.sort_values(["year", "brma", "lha_category", "weekly_rent"])


def build(cache: Path) -> pd.DataFrame:
    cache.mkdir(parents=True, exist_ok=True)
    rents = pd.read_csv(LIST_OF_RENTS_PATH)
    scotland = scottish_lists(fetch(SOURCE, cache))
    assert scotland.brma.nunique() == 18
    rents = pd.concat([rents[rents.region != "SCOTLAND"], scotland], ignore_index=True)
    return rents


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "lha")
    args = parser.parse_args(argv)
    rents = build(args.cache)
    rents.to_csv(
        LIST_OF_RENTS_PATH,
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    print(f"Wrote {len(rents):,} rents to {LIST_OF_RENTS_PATH}")
    return 0
