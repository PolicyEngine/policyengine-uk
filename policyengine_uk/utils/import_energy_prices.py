"""Write the published inputs of the household energy price indices.

``python -m policyengine_uk.utils.import_energy_prices`` reads four files and
rewrites ``ons.yaml``, ``obr.yaml`` and ``consumption_shares.yaml`` under
``policyengine_uk/parameters/gov/economic_assumptions/energy_prices``:

- ONS MM23, the consumer price inflation time series (CSV): the monthly CPI
  indices for electricity (D7DT), gas (D7DU) and electricity, gas and solid
  fuels (DK9U), and their annual CPI weights (CJXA, CJXB, A9F4), from 2015,
  with the last quarter ONS publishes all three months of in every series
  (``last_full_quarter``), where the generation step ends the outturn;
- the economy workbook of an OBR Economic and fiscal outlook's detailed
  forecast tables: Table 1.19's year-on-year CPI utilities inflation, for the
  quarters after the last one ONS publishes all three months of;
- DESNZ Energy Trends tables ET 5.2 (electricity) and ET 4.1 (gas): domestic
  consumption by quarter, averaged into each quarter's share of a year's
  consumption over the complete years from 2015.

The generation step ``add_energy_price_indices`` builds the indices from these
and from the hand-maintained ``embedded_electricity_vat.yaml``. The importer
writes every file or none, and rerunning it on the same sources reproduces the
committed files byte for byte.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

from policyengine_uk.utils.import_obr_forecasts import (
    build_efo_href,
    normalise_label,
    read_sheet_rows,
    resolve_release,
    write_all_or_none,
)

PARAMETER_DIR = (
    Path(__file__).resolve().parents[1]
    / "parameters"
    / "gov"
    / "economic_assumptions"
    / "energy_prices"
)
FIRST_YEAR = 2015
MM23_URL = (
    "https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/"
    "datasets/consumerpriceindices/current/mm23.csv"
)
ONS_SERIES_URL = (
    "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/{}/mm23"
)
ELECTRICITY_TRENDS_URL = (
    "https://www.gov.uk/government/statistics/electricity-section-5-energy-trends"
)
GAS_TRENDS_URL = "https://www.gov.uk/government/statistics/gas-section-4-energy-trends"
MONTHS = ("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC").split()
MONTH_ROW = re.compile(r"^(\d{4}) ([A-Z]{3})$")
YEAR_ROW = re.compile(r"^(\d{4})$")
QUARTER_COLUMN = re.compile(r"^(\d{4})\s+(1st|2nd|3rd|4th) quarter")
QUARTER_NUMBER = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4}
QUARTER_ROW = re.compile(r"^(\d{4})\s*Q([1-4])$")
QUARTER_MONTHS = {1: "January to March", 2: "April to June"}
QUARTER_MONTHS.update({3: "July to September", 4: "October to December"})


@dataclass(frozen=True)
class OnsSeries:
    key: str
    cdid: str
    weight_cdid: str
    name: str
    coicop: str


ONS_SERIES = (
    OnsSeries("electricity", "D7DT", "CJXA", "electricity", "class 04.5.1"),
    OnsSeries("gas", "D7DU", "CJXB", "gas", "class 04.5.2"),
    OnsSeries(
        "electricity_gas_and_solid_fuels",
        "DK9U",
        "A9F4",
        "electricity, gas and solid fuels",
        "classes 04.5.1, 04.5.2 and 04.5.4",
    ),
)


@dataclass(frozen=True)
class Mm23:
    release: date
    monthly: dict[str, dict[tuple[int, int], str]]
    annual: dict[str, dict[int, str]]


def read_mm23(text: str) -> Mm23:
    """The monthly indices and annual weights the energy indices use.

    Values keep the text ONS publishes, so the YAML states them unchanged.
    """
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 8 or rows[1][:1] != ["CDID"]:
        raise ValueError("Not an MM23 CSV: the second row must hold the CDIDs.")
    columns = {cdid: index for index, cdid in enumerate(rows[1])}
    labels = {row[0]: row for row in rows if row}
    wanted = [series.cdid for series in ONS_SERIES]
    wanted += [series.weight_cdid for series in ONS_SERIES]
    missing = [cdid for cdid in wanted if cdid not in columns]
    if missing:
        raise ValueError(f"MM23 has no column for {', '.join(missing)}.")
    releases = {labels["Release Date"][columns[cdid]] for cdid in wanted}
    if len(releases) != 1:
        raise ValueError(f"MM23 series come from different releases: {releases}.")
    release = datetime.strptime(releases.pop(), "%d-%m-%Y").date()

    monthly: dict[str, dict[tuple[int, int], str]] = {}
    annual: dict[str, dict[int, str]] = {}
    for series in ONS_SERIES:
        monthly[series.cdid] = {}
        annual[series.weight_cdid] = {}
    for row in rows[7:]:
        if not row:
            continue
        month = MONTH_ROW.match(row[0])
        year = YEAR_ROW.match(row[0])
        for series in ONS_SERIES:
            if month and int(month.group(1)) >= FIRST_YEAR:
                value = row[columns[series.cdid]].strip()
                if value:
                    float(value)
                    key = (int(month.group(1)), MONTHS.index(month.group(2)) + 1)
                    monthly[series.cdid][key] = value
            if year and int(year.group(1)) >= FIRST_YEAR:
                value = row[columns[series.weight_cdid]].strip()
                if value:
                    float(value)
                    annual[series.weight_cdid][int(year.group(1))] = value
    for series in ONS_SERIES:
        months = sorted(monthly[series.cdid])
        expected = [
            (year, month)
            for year in range(FIRST_YEAR, months[-1][0] + 1)
            for month in range(1, 13)
            if (year, month) <= months[-1]
        ]
        if months != expected:
            raise ValueError(f"MM23 {series.cdid} has gaps after {FIRST_YEAR}.")
    return Mm23(release=release, monthly=monthly, annual=annual)


def last_complete_quarter(mm23: Mm23) -> tuple[int, int]:
    """The last quarter ONS publishes all three months of, in every series."""
    last = min(max(values) for values in mm23.monthly.values())
    year, month = last
    quarter = month // 3
    if quarter == 0:
        return year - 1, 4
    return year, quarter


def read_obr_utilities(xlsx_bytes: bytes) -> dict[tuple[int, int], float]:
    """Table 1.19's utilities inflation, year on year, as fractions."""
    rows = read_sheet_rows(xlsx_bytes, "1.19")
    if not any(
        "cpi category inflation" in normalise_label(value)
        for row in rows[:3]
        for value in row.values()
    ):
        raise ValueError("Sheet 1.19 is not the CPI category inflation table.")
    columns = [
        column
        for row in rows[:5]
        for column, value in row.items()
        if normalise_label(value) == "utilities"
    ]
    if len(columns) != 1:
        raise ValueError("Table 1.19 must have exactly one Utilities column.")
    values = {}
    for row in rows:
        label = QUARTER_ROW.match(str(row.get("B") or "").strip())
        raw = row.get(columns[0])
        if label and raw not in (None, ""):
            values[(int(label.group(1)), int(label.group(2)))] = float(raw) / 100
    if not values:
        raise ValueError("Table 1.19 has no quarterly utilities inflation.")
    return values


def read_domestic_consumption(
    xlsx_bytes: bytes, sheet: str, row_label: str
) -> dict[tuple[int, int], float]:
    """Domestic consumption by quarter from an Energy Trends quarterly sheet."""
    rows = read_sheet_rows(xlsx_bytes, sheet)
    headers = {}
    for row in rows[:10]:
        for column, value in row.items():
            match = QUARTER_COLUMN.match(" ".join(str(value or "").split()))
            if match:
                quarter = QUARTER_NUMBER[match.group(2)]
                headers[column] = (int(match.group(1)), quarter)
    matches = [row for row in rows if str(row.get("A") or "").strip() == row_label]
    if not headers or len(matches) != 1:
        raise ValueError(f"Could not find one {row_label!r} row in sheet {sheet}.")
    return {
        quarter: float(matches[0][column])
        for column, quarter in headers.items()
        if matches[0].get(column) not in (None, "")
    }


def seasonal_shares(
    consumption: dict[tuple[int, int], float],
) -> tuple[list[float], int]:
    """Mean share of each quarter in a year's consumption, from 2015.

    Uses each complete calendar year from 2015. Returns the four shares,
    rounded to four decimal places, and the last year averaged.
    """
    years = [
        year
        for year in range(FIRST_YEAR, max(year for year, _ in consumption) + 1)
        if all((year, quarter) in consumption for quarter in range(1, 5))
    ]
    if not years or years != list(range(FIRST_YEAR, years[-1] + 1)):
        raise ValueError("Domestic consumption must run in complete years from 2015.")
    shares = [0.0] * 4
    for year in years:
        total = sum(consumption[(year, quarter)] for quarter in range(1, 5))
        for quarter in range(1, 5):
            shares[quarter - 1] += consumption[(year, quarter)] / total / len(years)
    return [round(share, 4) for share in shares], years[-1]


def _long_date(day: date) -> str:
    return f"{day.day} {day.strftime('%B')} {day.year}"


def render_ons_yaml(mm23: Mm23) -> str:
    released = _long_date(mm23.release)
    year, quarter = last_complete_quarter(mm23)
    lines = [
        "# policyengine_uk/utils/import_energy_prices.py writes this file from ONS MM23.",
        "# Rerun the importer on a new MM23 release; do not edit by hand.",
        "description: ONS consumer prices index series that the household energy "
        "price indices build on.",
        "metadata:",
        "  # The last quarter ONS publishes all three months of in every series.",
        "  # The indices use the prices to its end and the OBR forecast after it;",
        "  # a reform to the prices cannot move it.",
        f"  last_full_quarter: {year}Q{quarter}",
    ]
    for series in ONS_SERIES:
        lines += [
            f"{series.key}:",
            f"  description: ONS CPI index for {series.name} ({series.coicop}, "
            f"series {series.cdid}), monthly, 2015 = 100. The prices include VAT "
            "at the rate in force.",
            "  metadata:",
            f"    label: CPI index for {series.name} (ONS {series.cdid})",
            "    period: month",
            "    reference:",
            f"      - title: ONS, Consumer price inflation time series (MM23), "
            f"series {series.cdid}, released {released}",
            f"        href: {ONS_SERIES_URL.format(series.cdid.lower())}",
            "  values:",
        ]
        for (year, month), value in sorted(mm23.monthly[series.cdid].items()):
            lines.append(f"    {year:04d}-{month:02d}-01: {value}")
    lines += [
        "weights:",
        "  description: ONS CPI weights of the series, in parts per thousand of "
        "the CPI, by calendar year.",
    ]
    for series in ONS_SERIES:
        lines += [
            f"  {series.key}:",
            f"    description: CPI weight of {series.name} ({series.coicop}, "
            f"series {series.weight_cdid}), parts per thousand.",
            "    metadata:",
            f"      label: CPI weight of {series.name} (ONS {series.weight_cdid})",
            "      period: year",
            "      reference:",
            f"        - title: ONS, Consumer price inflation time series (MM23), "
            f"series {series.weight_cdid}, released {released}",
            f"          href: {ONS_SERIES_URL.format(series.weight_cdid.lower())}",
            "    values:",
        ]
        for year, value in sorted(mm23.annual[series.weight_cdid].items()):
            lines.append(f"      {year:04d}-01-01: {value}")
    return "\n".join(lines) + "\n"


def render_obr_yaml(
    utilities: dict[tuple[int, int], float],
    after: tuple[int, int],
    release: tuple[str, int],
) -> str:
    month, year = release
    forecast = {
        quarter: value for quarter, value in utilities.items() if quarter > after
    }
    if not forecast:
        raise ValueError(f"Table 1.19 has no quarter after {after[0]}Q{after[1]}.")
    quarters = sorted(forecast)
    expected = []
    quarter = quarters[0]
    while quarter <= quarters[-1]:
        expected.append(quarter)
        quarter = (quarter[0] + quarter[1] // 4, quarter[1] % 4 + 1)
    if quarters != expected:
        raise ValueError("Table 1.19's forecast quarters have gaps.")
    first = f"{quarters[0][0]}Q{quarters[0][1]}"
    lines = [
        "# policyengine_uk/utils/import_energy_prices.py writes this file from the",
        "# OBR economy tables. Rerun the importer on a new EFO; do not edit by hand.",
        "description: OBR forecasts that the household energy price indices build on.",
        "utilities:",
        "  description: OBR forecast of CPI utilities inflation (electricity and "
        "gas), year on year, by calendar quarter, from the first quarter ONS has "
        f"not published in full ({first}). The OBR's published rate, so it "
        "includes the measures the OBR forecast includes; the generation step "
        "removes the electricity VAT change.",
        "  metadata:",
        "    unit: /1",
        "    label: OBR forecast of CPI utilities inflation",
        "    period: quarter",
        "    reference:",
        f"      - title: OBR, Economic and fiscal outlook, {month} {year}, "
        "detailed forecast tables (economy), Table 1.19",
        f"        href: {build_efo_href(month, year)}",
        "  values:",
    ]
    for year_, quarter_ in quarters:
        value = round(forecast[(year_, quarter_)], 6) + 0.0
        lines.append(f"    {year_:04d}-{3 * quarter_ - 2:02d}-01: {value:.6f}")
    return "\n".join(lines) + "\n"


def render_consumption_shares_yaml(
    shares: dict[str, tuple[list[float], int]],
) -> str:
    sources = {
        "electricity": (
            "electricity",
            "ET 5.2 (Quarter sheet, Domestic (excluding electric vehicles))",
            "Energy Trends UK electricity",
            ELECTRICITY_TRENDS_URL,
        ),
        "gas": (
            "gas",
            "ET 4.1 (Quarter (GWh) sheet, Domestic)",
            "Energy Trends UK gas",
            GAS_TRENDS_URL,
        ),
    }
    lines = [
        "# policyengine_uk/utils/import_energy_prices.py writes this file from",
        "# DESNZ Energy Trends. Rerun the importer on new tables; do not edit by hand.",
        "description: Shares of a year's domestic energy consumption in each "
        "calendar quarter, which weight quarterly price levels into annual ones.",
    ]
    for key, (name, table, title, href) in sources.items():
        values, last_year = shares[key]
        lines += [
            f"{key}:",
            f"  description: Mean share of each calendar quarter in a year's UK "
            f"domestic {name} consumption, {FIRST_YEAR} to {last_year}.",
        ]
        for quarter, value in enumerate(values, start=1):
            lines += [
                f"  q{quarter}:",
                f"    description: Share of a year's domestic {name} consumption "
                f"that households use in {QUARTER_MONTHS[quarter]}.",
                "    metadata:",
                "      unit: /1",
                f"      label: Domestic {name} consumption share, quarter {quarter}",
                "      period: year",
                "      reference:",
                f"        - title: DESNZ, {title}, {table}, mean of {FIRST_YEAR} "
                f"to {last_year}",
                f"          href: {href}",
                "    values:",
                f"      {FIRST_YEAR}-01-01: {value:.4f}",
            ]
    return "\n".join(lines) + "\n"


def render_all(
    mm23_text: str,
    obr_bytes: bytes,
    obr_name: str,
    electricity_trends: bytes,
    gas_trends: bytes,
) -> dict[str, str]:
    mm23 = read_mm23(mm23_text)
    release = resolve_release(obr_bytes, obr_name)
    if release is None:
        raise ValueError(f"Could not tell which EFO {obr_name} comes from.")
    shares = {
        "electricity": seasonal_shares(
            read_domestic_consumption(
                electricity_trends,
                "Quarter",
                "Domestic (excluding electric vehicles)",
            )
        ),
        "gas": seasonal_shares(
            read_domestic_consumption(gas_trends, "Quarter (GWh)", "Domestic")
        ),
    }
    outputs = {
        "ons.yaml": render_ons_yaml(mm23),
        "obr.yaml": render_obr_yaml(
            read_obr_utilities(obr_bytes), last_complete_quarter(mm23), release
        ),
        "consumption_shares.yaml": render_consumption_shares_yaml(shares),
    }
    for text in outputs.values():
        # Fails on text a source could make invalid YAML, before any write.
        yaml.safe_load(text)
    return outputs


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mm23", required=True, help=f"ONS MM23 CSV ({MM23_URL})")
    parser.add_argument(
        "--obr-economy",
        required=True,
        help="OBR detailed forecast tables, economy workbook (.xlsx)",
    )
    parser.add_argument(
        "--electricity-trends", required=True, help="DESNZ ET 5.2 workbook (.xlsx)"
    )
    parser.add_argument(
        "--gas-trends", required=True, help="DESNZ ET 4.1 workbook (.xlsx)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PARAMETER_DIR,
        help="Directory to write the YAML files to",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    obr = Path(args.obr_economy).expanduser()
    outputs = render_all(
        Path(args.mm23).expanduser().read_text(encoding="utf-8-sig"),
        obr.read_bytes(),
        obr.name,
        Path(args.electricity_trends).expanduser().read_bytes(),
        Path(args.gas_trends).expanduser().read_bytes(),
    )
    write_all_or_none({args.output_dir / name: text for name, text in outputs.items()})
    for name in outputs:
        print(f"Wrote {args.output_dir / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
