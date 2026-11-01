from __future__ import annotations

import argparse
import copy
import math
import os
import re
import shutil
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET

import yaml

WORKBOOK_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
YEAR_RE = re.compile(r"^\d{4}$")
MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)
MONTH_RE = re.compile(rf"({'|'.join(MONTHS)})[-_ ]+(\d{{4}})", re.IGNORECASE)


@dataclass(frozen=True)
class SeriesSpec:
    key: str
    sheet: str
    table: str
    column: str
    mode: str
    needles: tuple[str, ...]


SERIES_SPECS = (
    SeriesSpec(
        key="average_earnings",
        sheet="1.6",
        table="1.6",
        column="Q",
        mode="contains",
        needles=("average weekly earnings growth",),
    ),
    SeriesSpec(
        key="rpi",
        sheet="1.7",
        table="1.7",
        column="C",
        mode="exact",
        needles=("rpi",),
    ),
    SeriesSpec(
        key="consumer_price_index",
        sheet="1.7",
        table="1.7",
        column="E",
        mode="exact",
        needles=("cpi",),
    ),
    SeriesSpec(
        key="cpih",
        sheet="1.7",
        table="1.7",
        column="F",
        mode="exact",
        needles=("cpih",),
    ),
    SeriesSpec(
        key="mortgage_interest",
        sheet="1.7",
        table="1.7",
        column="H",
        mode="contains",
        needles=("mortgage interest",),
    ),
    SeriesSpec(
        key="rent",
        sheet="1.7",
        table="1.7",
        column="I",
        mode="contains",
        needles=("actual rents",),
    ),
    SeriesSpec(
        key="house_prices",
        sheet="1.16",
        table="1.16",
        column="D",
        mode="contains_all",
        needles=("house price index", "per cent change on a year earlier"),
    ),
)


QUARTER_RE = re.compile(r"^(\d{4})\s*Q([1-4])$")


@dataclass(frozen=True)
class StatutoryGapSpec:
    """Forecast gap between a statutory uprating input and calendar-year growth.

    The OBR publishes September CPI only as the receipts tables' memo row of
    the CPI used to uprate tax thresholds, and does not forecast May-July AWE
    at all. Where the September row is not supplied or does not cover a year,
    the statutory figure is the quarter containing (or nearest) the statutory
    period, from the same economy-table column as the calendar-year figure.
    """

    key: str
    series_key: str
    quarter: int
    month_day: str
    description: str


STATUTORY_GAP_SPECS = (
    StatutoryGapSpec(
        key="cpi_september",
        series_key="consumer_price_index",
        quarter=3,
        month_day="09-01",
        description="Q3 CPI 12-month rate",
    ),
    StatutoryGapSpec(
        key="awe_total_pay_may_july",
        series_key="average_earnings",
        quarter=2,
        month_day="07-01",
        description="Q2 average earnings growth on a year earlier",
    ),
)


def get_repo_root() -> Path:
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "policyengine_uk").is_dir():
            return current
        current = current.parent
    raise RuntimeError("Could not find repository root")


def get_yoy_growth_path() -> Path:
    return (
        get_repo_root()
        / "policyengine_uk/parameters/gov/economic_assumptions/yoy_growth.yaml"
    )


def get_forecast_gap_dir(yoy_growth_path: Path | None = None) -> Path:
    """The forecast_gap directory next to a yoy_growth.yaml."""
    yoy_growth_path = yoy_growth_path or get_yoy_growth_path()
    return yoy_growth_path.parent / "statutory_uprating_inputs" / "forecast_gap"


def normalise_label(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).replace("\n", " ").split()).strip().lower()


def is_generic_header(label: str) -> bool:
    return label == "year-on-year growth" or bool(
        re.fullmatch(r"(jan )?\d{4}( ?= ?100)?", label)
    )


def read_url_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response:
        return response.read()


def load_source_bytes(url: str | None, file_path: str | None) -> tuple[str, bytes]:
    if bool(url) == bool(file_path):
        raise ValueError("Pass exactly one of --url or --file")

    if url:
        return url, read_url_bytes(url)

    path = Path(file_path).expanduser().resolve()
    return path.name, path.read_bytes()


def is_xlsx_bytes(data: bytes) -> bool:
    try:
        with ZipFile(BytesIO(data)) as archive:
            return "xl/workbook.xml" in archive.namelist()
    except BadZipFile:
        return False


def extract_economy_workbook_bytes(
    source_name: str, source_bytes: bytes
) -> tuple[str, bytes]:
    if is_xlsx_bytes(source_bytes):
        return source_name, source_bytes

    with ZipFile(BytesIO(source_bytes)) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".xlsx") and "economy" in Path(name).name.lower()
        ]
        if not candidates:
            raise ValueError("Could not find an economy workbook in the source")
        candidates.sort()
        workbook_name = candidates[0]
        return Path(workbook_name).name, archive.read(workbook_name)


def _load_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []

    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("main:si", WORKBOOK_NS):
        parts = [node.text or "" for node in item.iterfind(".//main:t", WORKBOOK_NS)]
        values.append("".join(parts))
    return values


def _sheet_paths(archive: ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in rels.findall("pkgrel:Relationship", WORKBOOK_NS)
    }

    result = {}
    for sheet in workbook.find("main:sheets", WORKBOOK_NS):
        rel_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        result[sheet.attrib["name"]] = f"xl/{rel_map[rel_id]}"
    return result


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str | None:
    value_node = cell.find("main:v", WORKBOOK_NS)
    inline_node = cell.find("main:is", WORKBOOK_NS)
    cell_type = cell.attrib.get("t")

    if cell_type == "s" and value_node is not None:
        return shared_strings[int(value_node.text)]
    if cell_type == "inlineStr" and inline_node is not None:
        text_node = inline_node.find(".//main:t", WORKBOOK_NS)
        return text_node.text if text_node is not None else ""
    if value_node is not None:
        return value_node.text
    return None


def read_sheet_rows(xlsx_bytes: bytes, sheet_name: str) -> list[dict[str, str | None]]:
    with ZipFile(BytesIO(xlsx_bytes)) as archive:
        shared_strings = _load_shared_strings(archive)
        sheet_path = _sheet_paths(archive)[sheet_name]
        sheet = ET.fromstring(archive.read(sheet_path))

    rows = []
    for row in sheet.findall(".//main:sheetData/main:row", WORKBOOK_NS):
        values: dict[str, str | None] = {}
        for cell in row.findall("main:c", WORKBOOK_NS):
            ref = cell.attrib["r"]
            column = "".join(ch for ch in ref if ch.isalpha())
            values[column] = _cell_value(cell, shared_strings)
        rows.append(values)
    return rows


def find_series_column(rows: list[dict[str, str | None]], spec: SeriesSpec) -> str:
    headers: dict[str, str] = {}
    for row in rows[:4]:
        for column, value in row.items():
            label = normalise_label(value)
            if label and (column not in headers or is_generic_header(headers[column])):
                headers[column] = label

    header = headers.get(spec.column, "")
    if spec.mode == "exact" and header in spec.needles:
        return spec.column
    if spec.mode == "contains" and any(needle in header for needle in spec.needles):
        return spec.column
    if spec.mode == "contains_all" and all(needle in header for needle in spec.needles):
        return spec.column

    raise ValueError(f"Could not find a column for {spec.key} in sheet {spec.sheet}")


def extract_annual_series_from_xlsx(
    xlsx_bytes: bytes,
) -> dict[str, dict[int, float]]:
    rows_by_sheet = {
        sheet: read_sheet_rows(xlsx_bytes, sheet)
        for sheet in {spec.sheet for spec in SERIES_SPECS}
    }

    result: dict[str, dict[int, float]] = {}
    for spec in SERIES_SPECS:
        rows = rows_by_sheet[spec.sheet]
        column = find_series_column(rows, spec)
        values: dict[int, float] = {}
        for row in rows:
            year_cell = row.get("B")
            if not year_cell or not YEAR_RE.match(str(year_cell)):
                continue
            year = int(str(year_cell))
            raw_value = row.get(column)
            if raw_value in (None, ""):
                continue
            values[year] = round(float(raw_value) / 100, 4)
        result[spec.key] = values
    return result


def extract_series_by_period_from_xlsx(
    xlsx_bytes: bytes, series_keys: set[str]
) -> dict[str, dict[str, float]]:
    """Full-precision values (as fractions) keyed by the row label in column B,
    e.g. "2026" or "2026Q3"."""
    specs = [spec for spec in SERIES_SPECS if spec.key in series_keys]
    rows_by_sheet = {
        sheet: read_sheet_rows(xlsx_bytes, sheet) for sheet in {s.sheet for s in specs}
    }
    result: dict[str, dict[str, float]] = {}
    for spec in specs:
        rows = rows_by_sheet[spec.sheet]
        column = find_series_column(rows, spec)
        values: dict[str, float] = {}
        for row in rows:
            label = str(row.get("B") or "").strip()
            raw_value = row.get(column)
            if not label or raw_value in (None, ""):
                continue
            if YEAR_RE.match(label) or QUARTER_RE.match(label):
                values[label.replace(" ", "")] = float(raw_value) / 100
        result[spec.key] = values
    return result


SEPTEMBER_CPI_LABEL = "cpi used to uprate thresholds"
FISCAL_YEAR_RE = re.compile(r"^(\d{4})-(\d{2})$")


@dataclass(frozen=True)
class ForecastGap:
    value: float
    source: str
    reference_title: str


def extract_september_cpi_from_receipts(
    xlsx_bytes: bytes,
) -> tuple[str, dict[int, float]]:
    """September CPI 12-month rates from the receipts tables.

    The OBR publishes them as the memo row "CPI used to uprate thresholds",
    one column per fiscal year of uprating: 2027-28 holds September 2026.
    Returns the table number and the rates keyed by September's year.
    """
    with ZipFile(BytesIO(xlsx_bytes)) as archive:
        sheet_names = list(_sheet_paths(archive))
    for sheet in sheet_names:
        rows = read_sheet_rows(xlsx_bytes, sheet)
        for index, row in enumerate(rows):
            if SEPTEMBER_CPI_LABEL not in normalise_label(row.get("B")):
                continue
            columns = {}
            for header in reversed(rows[:index]):
                columns = {
                    column: int(match.group(1))
                    for column, value in header.items()
                    if value and (match := FISCAL_YEAR_RE.match(str(value).strip()))
                }
                if columns:
                    break
            rates = {
                fiscal_year - 1: float(row[column]) / 100
                for column, fiscal_year in columns.items()
                if row.get(column) not in (None, "")
            }
            if rates:
                return sheet, rates
    raise ValueError("Could not find September CPI in the receipts workbook")


def compute_statutory_forecast_gaps(
    xlsx_bytes: bytes,
    forecast_start_year: int,
    forecast_years: int,
    receipts_xlsx_bytes: bytes | None = None,
    calendar_values: dict[str, dict[int, float]] | None = None,
) -> dict[str, dict[int, ForecastGap]]:
    """Gap for each statutory input and forecast year, rounded to 1e-5.

    The gap is the OBR's statutory-basis figure minus the calendar-year growth
    PolicyEngine stores, so that stored growth plus the gap reproduces the
    OBR figure. ``calendar_values`` defaults to the values this importer
    writes to yoy_growth.yaml. September CPI comes from the receipts tables
    where they are supplied and cover the year; otherwise each input uses its
    quarter from the economy tables.
    """
    series = extract_series_by_period_from_xlsx(
        xlsx_bytes, {spec.series_key for spec in STATUTORY_GAP_SPECS}
    )
    if calendar_values is None:
        calendar_values = extract_annual_series_from_xlsx(xlsx_bytes)
    september_table, september_cpi = (
        extract_september_cpi_from_receipts(receipts_xlsx_bytes)
        if receipts_xlsx_bytes is not None
        else (None, {})
    )
    gaps: dict[str, dict[int, ForecastGap]] = {}
    for spec in STATUTORY_GAP_SPECS:
        values = series[spec.series_key]
        calendar = calendar_values.get(spec.series_key, {})
        table = next(s.table for s in SERIES_SPECS if s.key == spec.series_key)
        gaps[spec.key] = {}
        for year in range(forecast_start_year, forecast_start_year + forecast_years):
            annual = calendar.get(year)
            if annual is None:
                continue
            if spec.key == "cpi_september" and year in september_cpi:
                statutory = september_cpi[year]
                source = (
                    f"September CPI (receipts Table {september_table}) minus "
                    "calendar-year CPI growth in yoy_growth.yaml"
                )
                reference = (
                    f"detailed forecast tables, receipts, Table {september_table}"
                )
            else:
                statutory = values.get(f"{year}Q{spec.quarter}")
                if statutory is None:
                    continue
                source = (
                    f"{spec.description} (economy Table {table}) minus "
                    "calendar-year growth in yoy_growth.yaml"
                )
                reference = f"detailed forecast tables, economy, Table {table}"
            gaps[spec.key][year] = ForecastGap(
                value=round(statutory - annual, 5) + 0.0,
                source=source,
                reference_title=reference,
            )
    return gaps


def read_calendar_values(yaml_path: Path) -> dict[str, dict[int, float]]:
    """Calendar-year growth by year for each series in a yoy_growth.yaml.

    Nested series are keyed by their path under ``obr`` joined with dots,
    such as ``stamp_duty_land_tax.residential``.
    """
    return _calendar_values(yaml.safe_load(yaml_path.read_text())["obr"])


def _calendar_values(node: dict, prefix: str = "") -> dict[str, dict[int, float]]:
    result = {}
    for key, child in node.items():
        if not isinstance(child, dict) or key == "metadata":
            continue
        if "values" in child:
            result[prefix + key] = {
                int(str(instant)[:4]): float(value)
                for instant, value in child["values"].items()
            }
        else:
            result.update(_calendar_values(child, f"{prefix}{key}."))
    return result


def format_gap(value: float) -> str:
    """Fixed-point text: YAML 1.1 reads exponent notation such as 3e-05 as a
    string."""
    if value == 0:
        return "0"
    text = f"{value:.5f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def render_forecast_gap_values(
    spec: StatutoryGapSpec, gaps: dict[int, ForecastGap], month: str, year: int
) -> str:
    """The values block of a forecast_gap YAML file."""
    if not gaps:
        raise ValueError(f"No forecast gaps for {spec.key}")
    lines = [
        "values:",
        "  # No gap applies to published years.",
        f"  2010-{spec.month_day}: 0",
    ]
    source = None
    for gap_year in sorted(gaps):
        if gaps[gap_year].source != source:
            source = gaps[gap_year].source
            lines.append(f"  # OBR EFO {month} {year}: {source}.")
        lines.append(
            f"  {gap_year}-{spec.month_day}: {format_gap(gaps[gap_year].value)}"
        )
    lines += [
        "  # After the EFO horizon: no gap, so the forecast is calendar-year growth.",
        f"  {max(gaps) + 1}-{spec.month_day}: 0",
    ]
    return "\n".join(lines) + "\n"


def render_forecast_gap_references(
    spec: StatutoryGapSpec, gaps: dict[int, ForecastGap], month: str, year: int
) -> str:
    table = next(s.table for s in SERIES_SPECS if s.key == spec.series_key)
    titles = [f"detailed forecast tables, economy, Table {table}"]
    for gap in gaps.values():
        if gap.reference_title not in titles:
            titles.append(gap.reference_title)
    lines = ["  reference:"]
    for title in titles:
        lines += [
            f"    - title: OBR EFO {month} {year} ({title})",
            f"      href: {build_efo_href(month, year)}",
        ]
    return "\n".join(lines) + "\n"


def render_forecast_gap_yaml(
    content: str,
    spec: StatutoryGapSpec,
    gaps: dict[int, ForecastGap],
    month: str,
    year: int,
) -> str:
    """Rewrite the values block and the reference list (the last metadata key),
    and check every value loads as a number."""
    values_pattern = re.compile(
        r"^values:\n.*?(?=^metadata:)", re.MULTILINE | re.DOTALL
    )
    content, values_count = values_pattern.subn(
        lambda _: render_forecast_gap_values(spec, gaps, month, year),
        content,
        count=1,
    )
    reference_pattern = re.compile(r"^  reference:\n.*\Z", re.MULTILINE | re.DOTALL)
    content, reference_count = reference_pattern.subn(
        lambda _: render_forecast_gap_references(spec, gaps, month, year),
        content,
        count=1,
    )
    if not (values_count and reference_count):
        raise ValueError(f"Could not find the values and reference for {spec.key}")
    loaded = yaml.safe_load(content)["values"]
    bad = {k: v for k, v in loaded.items() if not isinstance(v, (int, float))}
    if bad:
        raise ValueError(f"Non-numeric forecast gaps for {spec.key}: {bad}")
    return content


def update_forecast_gap_yaml(
    yaml_path: Path,
    spec: StatutoryGapSpec,
    gaps: dict[int, ForecastGap],
    month: str,
    year: int,
) -> None:
    yaml_path.write_text(
        render_forecast_gap_yaml(yaml_path.read_text(), spec, gaps, month, year)
    )


TABLE_TITLE_RE = re.compile(r"^(\d+\.\d+)\s+(.+)$")
TABLE_NUMBER_RE = re.compile(r"\d+\.\d+")
FOOTNOTE_RE = re.compile(r"(?<=[a-z])\d+$", re.IGNORECASE)
VALUE_LINE_RE = re.compile(r"^\s*(\d{4})-\d{2}-\d{2}:")
# The last year any growth series reaches: yoy_growth.yaml's last entries are
# for 2073, and lag_source_years runs a lagged series a year past its source.
# create_economic_assumption_indices stops at or before 2074, so a series that
# stays positive to here stays positive in the model.
LAST_INDEX_YEAR = 2074


@dataclass(frozen=True)
class RateComponent:
    """A part of a duty's base and the rate parameter the model charges on it.

    ``parameter`` is the rate's path in the model's parameter tree, such as
    ``gov.hmrc.gambling_duty.remote_gaming.rate``. ``weight`` is the part's
    size, in any unit: divided by the total of a line's weights, it is the
    part's share of the base, held at that share in every year.

    A part with a ``switch``, the path of a dated true-or-false parameter,
    pays the rate at ``switched`` on the days the switch is true, as the
    model's formula does for a part that moves between rates.
    """

    parameter: str
    weight: float = 1.0
    switch: str | None = None
    switched: str | None = None

    def __post_init__(self):
        if (self.switch is None) != (self.switched is None):
            raise ValueError(
                f"{self.parameter}: a switched part needs both a switch and "
                "the rate it switches to"
            )

    @property
    def paths(self) -> tuple[str, ...]:
        """The parameters the part's rate reads."""
        return tuple(
            path
            for path in (self.parameter, self.switch, self.switched)
            if path is not None
        )


@dataclass(frozen=True)
class ReceiptsOutturn:
    """A line's outturn receipts from outside the EFOs, in £ thousand (as
    published) by the calendar year in which each fiscal year starts.
    ``source`` names them in comments and ``title`` in references."""

    source: str
    title: str
    href: str
    receipts_thousands: tuple[tuple[int, float], ...]


@dataclass(frozen=True)
class ReceiptsSeriesSpec:
    """A line of the OBR receipts tables, grown by a yoy_growth.yaml series.

    ``path`` is the series' place under ``obr``. The table is found by its
    title, not its number, because numbers move between EFOs: current
    receipts on a cash basis are Table 3.8 in March 2026 and 3.9 in March
    2025. Titles and row labels are compared lowercased, without footnote
    markers.

    A line with ``rates`` grows a duty's base rather than its receipts, so a
    rate change the model applies itself moves receipts only once. Each
    year's base is its receipts over the rate the model charges in that
    fiscal year (see ``line_rate``). A year whose rate is zero has no base,
    so the series holds the base flat into and out of it. A line with
    ``outturn`` takes the years before the EFO's first from it, not from the
    previous EFO, which it does not read. ``references`` are cited after the
    sources of the levels.

    A series under ``per_capita`` grows its line per head (``per_head``).
    """

    path: tuple[str, ...]
    title: str
    row: str
    rates: tuple[RateComponent, ...] = ()
    outturn: ReceiptsOutturn | None = None
    references: tuple[tuple[str, str], ...] = ()

    @property
    def per_head(self) -> bool:
        """Whether the series sits under ``per_capita``. Dataset projection
        grows household weights by ``ons.population``, so
        ``render_receipts_growth_yaml`` writes such a series' growth over one
        plus that growth (``per_head_growth``, ``per_head_tail``), and the
        weighted total grows with the line in every year."""
        return self.path[0] == "per_capita"


GAMBLING_RATES = "gov.hmrc.gambling_duty"
MACHINE_GAMES = f"{GAMBLING_RATES}.machine_games"

# The higher-stake share of Machine Games Duty's standard-rate base: the part
# from machines with a maximum charge above £1 or a maximum prize above £100,
# which pays the higher rate from 1 April 2027 (#2731). It is the Gambling
# Commission's 2024-25 gaming machine yield in Category B over that in
# Categories B and C, £ million (Industry Statistics, April 2025 to March
# 2026 release, sheet 4, cells K34 and L34, revised). Category B holds the
# machines outside Categories C and D, and Category C's limits are a £1
# charge and a £100 prize. Category D machines either offer no cash prize,
# so their games are not dutiable, or charge at most 20p for at most £10 in
# cash, the lower-rate class (Finance Act 2012, Schedule 24, paragraphs 2(2)
# and 5(2)). The statistics cover only the premises the Commission licenses
# in Great Britain, not pubs, clubs or Northern Ireland: see
# docs/engineering/gambling-duties.md for how that bears on the share.
MACHINE_GAMES_HIGHER_STAKE_SHARE = 2_289.84969448829 / (
    2_289.84969448829 + 232.47489298159996
)


def gambling_spec(
    key: str,
    row: str,
    rates: tuple[RateComponent, ...],
    receipts_thousands: tuple[tuple[int, float], ...],
    **extra,
) -> ReceiptsSeriesSpec:
    """A betting and gaming duty's base per head (#2738): its line in the
    receipts tables' forecast breakdown (Table 4.10 in October 2026, 3.10 in
    March 2026), which publishes forecasts only, after HMRC's outturn. The
    model's gambling inputs start in 2024-25, the first year here."""
    return ReceiptsSeriesSpec(
        path=("per_capita", "gambling_duty_bases", key),
        title="betting and gaming duties forecast breakdown",
        row=row,
        rates=rates,
        outturn=ReceiptsOutturn(
            source="HMRC's receipts (July 2026 Betting and Gaming tables, "
            "Table_1_BG_receipts)",
            title="HMRC UK Betting and Gaming Statistics, July 2026 tables "
            "(Table_1_BG_receipts, 2024-25 and 2025-26 receipts)",
            href="https://assets.publishing.service.gov.uk/media/"
            "6ab54fd9fe72ed1e2b02f06b/2026_Jul_Bet_and_Gam_Tab.ods",
            receipts_thousands=receipts_thousands,
        ),
        **extra,
    )


def machine_games_spec(higher_stake_share: float) -> ReceiptsSeriesSpec:
    """Machine Games Duty's base. Each band's weight is its 2024-25 base (£):
    HMRC's liabilities (Table_2_MGD row 20) over its rate. Table 4.10's line
    includes Autumn Budget 2026's higher rate on higher-stake machines
    (paragraph 4.45), so ``higher_stake_share`` of the standard-rate band
    pays the higher rate on the days the model's switch is on, as
    ``machine_games_duty`` charges a higher-stake input at that share."""
    standard = 3_023_740_000
    return gambling_spec(
        "machine_games",
        "machine games duty",
        (
            RateComponent(f"{MACHINE_GAMES}.rates.lower", 138_420_000),
            RateComponent(
                f"{MACHINE_GAMES}.rates.standard", standard * (1 - higher_stake_share)
            ),
            RateComponent(
                f"{MACHINE_GAMES}.rates.standard",
                standard * higher_stake_share,
                switch=f"{MACHINE_GAMES}.higher_stake_machines_at_higher_rate",
                switched=f"{MACHINE_GAMES}.rates.higher",
            ),
            RateComponent(f"{MACHINE_GAMES}.rates.higher", 2_384_000),
        ),
        ((2024, 609_245), (2025, 641_010)),
        references=(
            (
                "Gambling Commission, Industry Statistics, April 2025 to March "
                "2026 (sheet 4, 2024-25 gaming machine yield by category)",
                "https://www.gamblingcommission.gov.uk/statistics-and-research/"
                "publication/industry-statistics-annual-report-financial-year-april-"
                "2025-to-march-2026-official-statistics",
            ),
        ),
    )


RECEIPTS_SERIES_SPECS = (
    ReceiptsSeriesSpec(
        path=("stamp_duty_land_tax", "residential"),
        title="property transactions taxes: receipts by sector",
        row="sdlt from residential property",
    ),
    ReceiptsSeriesSpec(
        path=("stamp_duty_land_tax", "non_residential"),
        title="property transactions taxes: receipts by sector",
        row="sdlt from non-residential property",
    ),
    ReceiptsSeriesSpec(
        path=("business_rates", "great_britain"),
        title="current receipts (on a cash basis)",
        row="business rates",
    ),
    ReceiptsSeriesSpec(
        path=("business_rates", "northern_ireland"),
        title="other taxes",
        row="northern ireland business rates",
    ),
    # The seven betting and gaming duties' bases. HMRC's receipts are row 45
    # (2024-25) and row 46 (2025-26) of Table_1_BG_receipts, £ thousand.
    gambling_spec(
        "remote_gaming",
        "remote gaming duty",
        (RateComponent(f"{GAMBLING_RATES}.remote_gaming.rate"),),
        ((2024, 1_162_539), (2025, 1_320_966)),
    ),
    gambling_spec(
        "lottery",
        "lottery duty",
        (RateComponent(f"{GAMBLING_RATES}.lottery.rate"),),
        ((2024, 931_887), (2025, 980_132)),
    ),
    # Each part's 2024-25 base (£): HMRC's General Betting Duty receipts over
    # 15%, split by the Gambling Commission's 2024-25 gross gambling yield as
    # Microcosm splits the model's inputs. Fixed odds take remote UK horse
    # racing, land-based fixed odds and racing pools. Microcosm's split gives
    # spread betting no part, so it has no weight.
    gambling_spec(
        "general_betting",
        "general betting duty",
        (
            RateComponent(
                f"{GAMBLING_RATES}.general_betting.rates.fixed_odds", 2_471_124_767
            ),
            RateComponent(
                f"{GAMBLING_RATES}.general_betting.rates.remote", 2_163_978_657
            ),
            RateComponent(
                f"{GAMBLING_RATES}.general_betting.rates.exchange_commission",
                123_949_909,
            ),
        ),
        ((2024, 713_858), (2025, 684_502)),
        references=(
            (
                "Microcosm, FY2024-25 General Betting Duty bases split by the "
                "Gambling Commission's gross gambling yield (docs/evidence/"
                "uk-excise-quantities-1359/outputs/national_reconciliation.json)",
                "https://github.com/PolicyEngine/microcosm/blob/main/docs/evidence/"
                "uk-excise-quantities-1359/outputs/national_reconciliation.json",
            ),
            (
                "Gambling Commission, industry statistics, April 2024 to March 2025",
                "https://www.gamblingcommission.gov.uk/statistics-and-research/"
                "publication/industry-statistics-annual-report-financial-year-april-"
                "2024-to-march-2025",
            ),
        ),
    ),
    machine_games_spec(MACHINE_GAMES_HIGHER_STAKE_SHARE),
    # The household Gaming Duty formula charges one effective rate, not the
    # statutory bands.
    gambling_spec(
        "gaming",
        "gaming duty",
        (RateComponent("household.consumption.gambling.casino_effective_rate"),),
        ((2024, 165_397), (2025, 173_902)),
    ),
    gambling_spec(
        "bingo",
        "bingo duty",
        (RateComponent(f"{GAMBLING_RATES}.bingo.rate"),),
        ((2024, 25_233), (2025, 26_073)),
    ),
    gambling_spec(
        "pool_betting",
        "pool betting duty",
        (RateComponent(f"{GAMBLING_RATES}.pool_betting.rate"),),
        ((2024, 8_125), (2025, 3_970)),
    ),
)


@lru_cache(maxsize=None)
def parameter_values(parameter: str) -> tuple[tuple[date, float], ...]:
    """A parameter's dated values, earliest first, from its file in the
    model's parameter tree. True and false read as 1 and 0."""
    path = get_repo_root() / "policyengine_uk/parameters" / Path(*parameter.split("."))
    values = yaml.safe_load(path.with_suffix(".yaml").read_text())["values"]
    entries = []
    for instant, value in values.items():
        if isinstance(value, dict):
            value = value["value"]
        entries.append((date.fromisoformat(str(instant)), float(value)))
    if not entries:
        raise ValueError(f"{parameter} has no values")
    return tuple(sorted(entries))


def value_on(parameter: str, day: date) -> float:
    """A parameter's value on ``day``. Before its first value it takes that
    value, as the model does: it backdates each parameter's first value."""
    entries = parameter_values(parameter)
    value = entries[0][1]
    for instant, entry in entries:
        if instant <= day:
            value = entry
    return value


def component_rate(component: RateComponent, day: date) -> float:
    """The rate a part of a base pays on ``day``."""
    if component.switch is not None and value_on(component.switch, day):
        return value_on(component.switched, day)
    return value_on(component.parameter, day)


def fiscal_year_rate(component: RateComponent, year: int) -> float:
    """A part's rate over the OBR's fiscal year ``year``, 1 April to 31
    March, averaged by days."""
    start, end = date(year, 4, 1), date(year + 1, 4, 1)
    changes = {
        instant
        for path in component.paths
        for instant, _ in parameter_values(path)
        if start < instant < end
    }
    bounds = [start, *sorted(changes), end]
    segments = [
        (component_rate(component, lower), (upper - lower).days)
        for lower, upper in zip(bounds, bounds[1:])
    ]
    if len({value for value, _ in segments}) == 1:
        return segments[0][0]
    return sum(value * days for value, days in segments) / (end - start).days


def line_rate(spec: ReceiptsSeriesSpec, year: int) -> float:
    """The rate the model charges on a line's base in fiscal year ``year``:
    its parts' fiscal-year rates, averaged by their weights."""
    total = sum(component.weight for component in spec.rates)
    return (
        sum(
            component.weight * fiscal_year_rate(component, year)
            for component in spec.rates
        )
        / total
    )


def growth_ratio(
    spec: ReceiptsSeriesSpec, levels: dict[int, float], year: int
) -> float:
    """One plus a line's growth into ``year``, before rounding: the ratio of
    its levels, or for a line with rates, of its bases, each year's receipts
    over the rate the model charges (``line_rate``). A year whose rate, or
    the year before's, is zero has no base, so the base holds flat."""
    if not spec.rates:
        return levels[year] / levels[year - 1]
    rate, previous_rate = line_rate(spec, year), line_rate(spec, year - 1)
    if rate == 0 or previous_rate == 0:
        return 1.0
    return (levels[year] / rate) / (levels[year - 1] / previous_rate)


@dataclass(frozen=True)
class ReceiptsLine:
    """A receipts line as one EFO publishes it: £bn by the calendar year in
    which each fiscal year starts, and which of those years are outturn."""

    table: str
    label: str
    levels: dict[int, float]
    outturn_years: frozenset[int]


@dataclass(frozen=True)
class ReceiptsGrowth:
    """Growth in a receipts line, by year, rounded to six decimals.

    The first year is outturn growth: this EFO's first (outturn) year over
    the year before in the previous EFO, where it is outturn. Each later
    year is the ratio of this EFO's consecutive levels. A line with its own
    outturn starts at that outturn's second year and has no previous line;
    one with rates grows its base instead (see ``ReceiptsSeriesSpec``).
    """

    values: dict[int, float]
    line: ReceiptsLine
    previous_line: ReceiptsLine | None
    spec: ReceiptsSeriesSpec | None = None


def fiscal_year_label(year: int) -> str:
    return f"{year}-{str(year + 1)[2:]}"


def column_index(column: str) -> int:
    index = 0
    for letter in column:
        index = index * 26 + ord(letter.upper()) - ord("A") + 1
    return index


def receipts_label(value: str | None) -> str:
    return FOOTNOTE_RE.sub("", normalise_label(value))


def read_workbook_sheets(xlsx_bytes: bytes) -> dict[str, list[dict[str, str | None]]]:
    with ZipFile(BytesIO(xlsx_bytes)) as archive:
        sheet_names = list(_sheet_paths(archive))
    return {sheet: read_sheet_rows(xlsx_bytes, sheet) for sheet in sheet_names}


def row_title(row: dict[str, str | None]) -> tuple[str, str] | None:
    """The number and normalised title of the table a row heads, e.g. ("3.8",
    "current receipts (on a cash basis)"), if its first non-empty cell is a
    table title."""
    for column in sorted(row, key=column_index):
        text = " ".join(str(row[column] or "").split())
        if text:
            match = TABLE_TITLE_RE.match(text)
            return (match.group(1), receipts_label(match.group(2))) if match else None
    return None


def sheet_tables(
    rows: list[dict[str, str | None]],
) -> list[tuple[str, str, list[dict[str, str | None]]]]:
    """Each table on a sheet: its number, normalised title and rows, from
    the row below its title to the row above the next title. Rows above the
    first title, such as a contents link or publication notes, are in no
    table."""
    tables = []
    for row in rows:
        title = row_title(row)
        if title is not None:
            tables.append((*title, []))
        elif tables:
            tables[-1][2].append(row)
    return tables


def _fiscal_year_columns(row: dict[str, str | None]) -> dict[str, int]:
    columns = {}
    for column, value in row.items():
        match = FISCAL_YEAR_RE.match(str(value or "").strip())
        if match and int(match.group(2)) == (int(match.group(1)) + 1) % 100:
            columns[column] = int(match.group(1))
    return columns


def _outturn_years(
    years: dict[str, int], markers: dict[str, int], where: str
) -> frozenset[int]:
    """Years from the "Outturn" marker's column up to the "Forecast" one.

    A table without an "Outturn" marker has no outturn years, and one
    without a "Forecast" marker no forecast years.
    """
    if not markers:
        raise ValueError(f"{where} does not mark its outturn and forecast years")
    if "outturn" not in markers:
        return frozenset()
    end = markers.get("forecast", float("inf"))
    return frozenset(
        year
        for column, year in years.items()
        if markers["outturn"] <= column_index(column) < end
    )


def validate_receipts_unit(
    header_rows: list[dict[str, str | None]], where: str
) -> None:
    """Require one explicit pound-billion declaration in this table's header.

    Only spelling, case and whitespace aliases of £ billion are supported.
    Requiring this same cash unit in every selected table in both releases
    prevents mixing magnitudes when their outturn levels are combined. A new
    magnitude, currency or real-terms measure needs deliberate importer support.
    """
    units = [
        normalise_label(value)
        for row in header_rows
        for value in row.values()
        if normalise_label(value) not in ("", "outturn", "forecast")
    ]
    if len(units) != 1:
        raise ValueError(
            f"{where} must declare exactly one receipts unit before its "
            f"fiscal-year header; found {units}"
        )
    if units[0] not in ("£ billion", "£bn", "£ bn"):
        raise ValueError(
            f"{where} has unsupported receipts unit {units[0]!r}; only "
            "£ billion (£bn or £ bn) is supported in both releases"
        )


def find_receipts_line(
    sheets: dict[str, list[dict[str, str | None]]], spec: ReceiptsSeriesSpec
) -> ReceiptsLine:
    """The one row labelled ``spec.row`` in a table titled ``spec.title``.

    Only that table's rows are read: its cash unit, year headers and its
    "Outturn" and "Forecast" markers, which may sit on one row or several.
    """
    matches = []
    for sheet, rows in sheets.items():
        for table, title, table_rows in sheet_tables(rows):
            if title != spec.title:
                continue
            where = f"Table {table} (sheet {sheet})"
            years: dict[str, int] = {}
            markers: dict[str, int] = {}
            header_rows = []
            for row in table_rows:
                row_years = _fiscal_year_columns(row)
                if row_years:
                    years = row_years
                    continue
                if not years:
                    header_rows.append(row)
                row_markers = [
                    (normalise_label(value), column_index(column))
                    for column, value in row.items()
                    if normalise_label(value) in ("outturn", "forecast")
                ]
                for marker, column in row_markers:
                    if markers.setdefault(marker, column) != column:
                        raise ValueError(
                            f'{where} marks "{marker.capitalize()}" in two '
                            "different columns"
                        )
                if row_markers:
                    continue
                if not years:
                    continue
                first_year_column = min(column_index(column) for column in years)
                labels = [
                    value
                    for column, value in sorted(
                        row.items(), key=lambda item: column_index(item[0])
                    )
                    if column_index(column) < first_year_column
                    and normalise_label(value)
                ]
                if labels and receipts_label(labels[0]) == spec.row:
                    matches.append(
                        (table, sheet, labels[0], row, years, markers, header_rows)
                    )

    name = ".".join(spec.path)
    if len(matches) != 1:
        found = ", ".join(f"sheet {match[1]}" for match in matches) or "none"
        raise ValueError(
            f'Expected one "{spec.row}" row in the "{spec.title}" table for '
            f"{name}; found {found}"
        )
    table, sheet, label, row, years, markers, header_rows = matches[0]
    where = f"Table {table} (sheet {sheet})"
    repeated = sorted({y for y in years.values() if list(years.values()).count(y) > 1})
    if repeated:
        raise ValueError(
            f"{where} heads more than one column "
            + ", ".join(fiscal_year_label(y) for y in repeated)
        )
    validate_receipts_unit(header_rows, where)
    levels = {}
    for column, year in years.items():
        text = row.get(column)
        try:
            levels[year] = float(text)
        except (TypeError, ValueError):
            raise ValueError(
                f"{where} has no numeric {fiscal_year_label(year)} {name} value: "
                f"{text!r}"
            ) from None
    ordered = sorted(levels)
    if ordered != list(range(ordered[0], ordered[-1] + 1)):
        raise ValueError(f"{where} skips a year: {ordered}")
    # The sheet name and the contents sheet number each table too, so a sheet
    # named as a table number gives the table's number, whatever its title
    # cell says: October 2026 titles sheet 4.8 "43.8 Current receipts (on a
    # cash basis)".
    if TABLE_NUMBER_RE.fullmatch(sheet):
        table = sheet
    return ReceiptsLine(
        table=table,
        label=FOOTNOTE_RE.sub("", " ".join(str(label).split())),
        levels=levels,
        outturn_years=_outturn_years(years, markers, where),
    )


def compute_receipts_growth(
    xlsx_bytes: bytes,
    previous_xlsx_bytes: bytes,
    specs: tuple[ReceiptsSeriesSpec, ...] = RECEIPTS_SERIES_SPECS,
) -> dict[tuple[str, ...], ReceiptsGrowth]:
    """Growth in each receipts line, from an EFO's receipts tables and an
    earlier EFO's, whose outturn is the base for the first year's growth.

    The first year must be outturn in this EFO, and the year before it
    outturn in the earlier one (March 2025 for March 2026). A line with its
    own outturn needs that outturn to reach the year before this EFO's
    first instead.
    """
    sheets = read_workbook_sheets(xlsx_bytes)
    previous_sheets = None
    result = {}
    for spec in specs:
        name = ".".join(spec.path)
        line = find_receipts_line(sheets, spec)
        first_year = min(line.levels)
        base_year = first_year - 1
        if spec.outturn is not None:
            previous = None
            outturn = {
                year: value / 1e6
                for year, value in spec.outturn.receipts_thousands
                if year < first_year
            }
            if base_year not in outturn:
                raise ValueError(
                    f"{name}: {spec.outturn.source} have no "
                    f"{fiscal_year_label(base_year)}, the year before Table "
                    f"{line.table}'s first; add them"
                )
            levels = {**outturn, **line.levels}
            if sorted(levels) != list(range(min(levels), max(levels) + 1)):
                raise ValueError(f"{name}: the outturn skips a year: {sorted(levels)}")
        else:
            if previous_sheets is None:
                previous_sheets = read_workbook_sheets(previous_xlsx_bytes)
            previous = find_receipts_line(previous_sheets, spec)
            if first_year not in line.outturn_years:
                raise ValueError(
                    f"{name}: {fiscal_year_label(first_year)}, the first year in "
                    f"Table {line.table}, is not outturn"
                )
            if base_year not in previous.outturn_years:
                raise ValueError(
                    f"{name}: the previous receipts tables have no "
                    f"{fiscal_year_label(base_year)} outturn; pass the EFO whose "
                    f"outturn year is {fiscal_year_label(base_year)}"
                )
            levels = {base_year: previous.levels[base_year], **line.levels}
        rates = {year: line_rate(spec, year) for year in levels} if spec.rates else {}
        # Growth to or from a level at or below zero means nothing, and a
        # zero last level would zero the series' index from then on. A year
        # whose rate is zero has no base to grow, whatever its receipts.
        for year, level in sorted(levels.items()):
            if level <= 0 and rates.get(year) != 0:
                raise ValueError(
                    f"{name}: {fiscal_year_label(year)} receipts of {level} are "
                    "not positive, so there is no growth to or from them"
                )
        values = {
            year: round(growth_ratio(spec, levels, year) - 1, 6) + 0.0
            for year in sorted(levels)[1:]
        }
        check_index(name, values)
        result[spec.path] = ReceiptsGrowth(values, line, previous, spec)
    return result


def check_index(name: str, values: dict[int, float]) -> None:
    """Refuse growth that zeroes the index the model builds from it.

    The model compounds the growth into an index rounded to five decimals
    (create_economic_assumption_indices), from 1 in a line's first year when
    the line has its own outturn. A positive base that rounds the index to
    zero would zero it in every later year.
    """
    index = 1.0
    for year, value in values.items():
        index = round(index * (1 + value), 5)
        if index <= 0:
            raise ValueError(
                f"{name}: {fiscal_year_label(year)} growth of {value} takes "
                f"the index to {index} at five decimals, so the base is "
                "too small to grow from"
            )


def population_growth(content: str) -> dict[int, float]:
    """``ons.population`` growth by year, as a yoy_growth.yaml holds it."""
    values = yaml.safe_load(content)["ons"]["population"]["values"]
    return dict(
        sorted(
            (int(str(instant)[:4]), float(value)) for instant, value in values.items()
        )
    )


def growth_in_effect(series: dict[int, float], year: int) -> float:
    """A growth series' value in ``year`` as the model reads it: its latest
    entry at or before the year, or its first entry before that, since the
    model backdates each parameter's first value."""
    earlier = [entry for entry in series if entry <= year]
    return series[max(earlier) if earlier else min(series)]


def per_head_growth(
    growth: ReceiptsGrowth, population: dict[int, float]
) -> ReceiptsGrowth:
    """A series' growth per head, to six decimals: each year's growth before
    rounding (``growth_ratio``), over one plus that year's ``ons.population``
    growth, minus one.

    Dataset projection grows each household's input by this and its weight
    by the population growth, so the weighted input grows by their product,
    the line's growth: a duty's base, for a line with rates.
    """
    spec = growth.spec
    first = min(growth.line.levels)
    if growth.previous_line is None:
        earlier = {
            year: value / 1e6
            for year, value in spec.outturn.receipts_thousands
            if year < first
        }
    else:
        earlier = {first - 1: growth.previous_line.levels[first - 1]}
    levels = {**earlier, **growth.line.levels}
    values = {
        year: round(
            growth_ratio(spec, levels, year) / (1 + growth_in_effect(population, year))
            - 1,
            6,
        )
        + 0.0
        for year in growth.values
    }
    check_index(".".join(growth.spec.path), values)
    return replace(growth, values=values)


def format_growth(value: float) -> str:
    """Fixed-point text with at least four decimals that reads back as the
    same float: 0.038 is written 0.0380, 1e-05 as 0.00001."""
    text = format(Decimal(repr(value + 0.0)), "f")
    whole, _, decimals = text.partition(".")
    return f"{whole}.{decimals.ljust(4, '0')}"


def average_earnings_path(content: str, after_year: int) -> dict[int, float]:
    """``average_earnings`` from the year after ``after_year``: its value in
    effect then and each later change, so a series given these values equals
    average_earnings in every later year."""
    values = yaml.safe_load(content)["obr"]["average_earnings"]["values"]
    entries = sorted((int(str(instant)[:4]), float(v)) for instant, v in values.items())
    start = after_year + 1
    in_effect = [value for year, value in entries if year <= start]
    if not in_effect:
        raise ValueError(f"average_earnings has no value in effect in {start}")
    path = {start: in_effect[-1]}
    for year, value in entries:
        if year > start and value != path[max(path)]:
            path[year] = value
    return path


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _yaml_block(
    lines: list[str], key: str, indent: int, start: int, end: int
) -> tuple[int, int]:
    """Lines [first, last) of the mapping entry ``key`` at ``indent`` within
    lines[start:end], from its key through its last non-blank child line.

    A comment indented no deeper than the key does not end the entry, as it
    does not in YAML; it is kept where it is, outside the entry's lines if it
    follows them."""
    pattern = re.compile(rf"^ {{{indent}}}{re.escape(key)}:(\s|$)")
    for first in range(start, end):
        if not pattern.match(lines[first]):
            continue
        last = first + 1
        for index in range(first + 1, end):
            if not lines[index].strip():
                continue
            if _indent(lines[index]) <= indent:
                if lines[index].lstrip().startswith("#"):
                    continue
                break
            last = index + 1
        return first, last
    raise ValueError(f"Could not find {key} at indent {indent}")


def _series_block(lines: list[str], path: tuple[str, ...]) -> tuple[int, int]:
    start, end = 0, len(lines)
    for depth, key in enumerate(path):
        start, end = _yaml_block(lines, key, 2 * depth, start, end)
    return start, end


def render_receipts_values(
    old_lines: list[str],
    indent: int,
    growth: ReceiptsGrowth,
    tail: dict[int, float],
    release: tuple[str, int],
    previous_release: tuple[str, int],
    tail_comment: str = "the average_earnings long-run path above",
) -> list[str]:
    """A series' values entries: earlier years as they were, then this
    EFO's growth, then the average_earnings path."""
    first_year = min(growth.values)
    kept: list[str] = []
    pending: list[str] = []
    for line in old_lines:
        match = VALUE_LINE_RE.match(line)
        if match is None:
            if line.strip() and not line.strip().startswith("#"):
                raise ValueError(f"Unexpected line in a values block: {line!r}")
            pending.append(line)
            continue
        if int(match.group(1)) < first_year:
            kept += pending + [line]
        pending = []

    month, year = release
    previous_month, previous_year = previous_release
    published, previous = growth.line, growth.previous_line
    efo_first = min(published.levels)
    pad = " " * indent
    first_kind = "Outturn" if efo_first in published.outturn_years else "Forecast"
    basis = receipts_basis(growth.spec)
    lines = list(kept)
    if previous is None:
        # The years before the EFO's first, and the base of its first, are
        # the line's own outturn.
        source = growth.spec.outturn.source
        years = sorted(y for y in growth.values if y < efo_first)
        if years:
            span = (
                f"{fiscal_year_label(years[0])} over {fiscal_year_label(years[0] - 1)}"
                if len(years) == 1
                else f"{years[0]}-{years[-1]}"
            )
            lines.append(f"{pad}# Outturn ({span}) from {source}{basis}")
            lines += [
                f"{pad}{y}-01-01: {format_growth(growth.values[y])}" for y in years
            ]
        lines.append(
            f"{pad}# {first_kind} ({fiscal_year_label(efo_first)} over "
            f"{fiscal_year_label(efo_first - 1)}) from OBR EFO {month} {year}, "
            f'receipts Table {published.table} "{published.label}", over '
            f"{source}{basis}"
        )
    else:
        table = f"Table {published.table}"
        if previous.table != published.table:
            table += f" ({previous_month} {previous_year}: Table {previous.table})"
        lines.append(
            f"{pad}# {first_kind} ({fiscal_year_label(efo_first)} over "
            f"{fiscal_year_label(efo_first - 1)}) from OBR EFO {month} {year} over "
            f'{previous_month} {previous_year}, receipts {table} "{published.label}"'
            f"{basis}"
        )
    lines.append(f"{pad}{efo_first}-01-01: {format_growth(growth.values[efo_first])}")
    later = sorted(y for y in growth.values if y > efo_first)
    for kind in ("Outturn", "Forecast"):
        years = [
            y for y in later if (y in published.outturn_years) == (kind == "Outturn")
        ]
        if not years:
            continue
        span = f"{years[0]}" if len(years) == 1 else f"{years[0]}-{years[-1]}"
        lines.append(
            f"{pad}# {kind} ({span}) from OBR EFO {month} {year}, receipts "
            f"Table {published.table}{basis}"
        )
        lines += [f"{pad}{y}-01-01: {format_growth(growth.values[y])}" for y in years]
    lines.append(f"{pad}# Beyond the OBR forecast: {tail_comment}")
    lines += [f"{pad}{y}-01-01: {format_growth(v)}" for y, v in sorted(tail.items())]
    return lines


def receipts_basis(spec: ReceiptsSeriesSpec | None) -> str:
    """How a line's growth is measured, for its comments: nothing for
    receipts, the rates taken out for a base, and population for a base per
    head."""
    if spec is None or not spec.rates:
        return ""
    if spec.per_head:
        return (
            "; per head: base growth (receipts over the rate the model charges) "
            "over one plus ons.population growth"
        )
    return "; base growth: receipts over the rate the model charges"


def per_head_tail(
    tail: dict[int, float], comment: str, population: dict[int, float]
) -> tuple[dict[int, float], str]:
    """A series' growth after the OBR's forecast per head, and its comment.

    In each year from the tail's first to the last that it or
    ``ons.population`` states, (1 + the tail's growth) / (1 + population
    growth) - 1, to six decimals, written where the value changes. The model
    holds each series' last value, so the weighted total grows by the tail in
    every later year too.
    """
    first = min(tail)
    yearly = {
        year: round(
            (1 + growth_in_effect(tail, year))
            / (1 + growth_in_effect(population, year))
            - 1,
            6,
        )
        + 0.0
        for year in range(first, max(max(tail), max(population), first) + 1)
    }
    return {
        year: value
        for year, value in yearly.items()
        if year == first or value != yearly[year - 1]
    }, f"{comment}; per head: (1 + that growth) / (1 + ons.population growth) - 1"


def receipts_tail(content: str, growth: ReceiptsGrowth) -> tuple[dict[int, float], str]:
    """A series' growth after the OBR's forecast, and its comment: the
    average_earnings path, held at zero in years a base's rate is zero in or
    comes from. A base under ``per_capita`` divides that growth by one plus
    ``ons.population`` growth (``per_head_tail``)."""
    last = max(growth.values)
    path = average_earnings_path(content, last)
    spec = growth.spec
    if spec is None or not spec.rates:
        return path, "the average_earnings long-run path above"
    # Rates hold their last value after their last change, as the path does.
    changes = [
        instant.year
        for component in spec.rates
        for parameter in component.paths
        for instant, _ in parameter_values(parameter)
    ]
    end = max(max(path), max(changes) + 1, last + 1)
    yearly = {}
    for year in range(last + 1, end + 1):
        if line_rate(spec, year) == 0 or line_rate(spec, year - 1) == 0:
            yearly[year] = 0.0
        else:
            yearly[year] = path[max(y for y in path if y <= year)]
    tail = {
        year: value
        for year, value in yearly.items()
        if year == last + 1 or value != yearly[year - 1]
    }
    if all(value == 0 for value in yearly.values()):
        comment = "held flat, as the rate is zero"
    elif any(value == 0 for value in yearly.values()):
        comment = (
            "the average_earnings long-run path above, held flat where the rate is zero"
        )
    else:
        comment = "the average_earnings long-run path above"
    if spec.per_head:
        return per_head_tail(tail, comment, population_growth(content))
    return tail, comment


def receipts_references(
    growth: ReceiptsGrowth,
    release: tuple[str, int],
    previous_release: tuple[str, int],
) -> list[dict[str, str]]:
    month, year = release
    previous_month, previous_year = previous_release
    current = {
        "title": f"OBR EFO {month} {year} (detailed forecast tables, receipts, "
        f"Table {growth.line.table})",
        "href": build_efo_href(month, year),
    }
    spec = growth.spec
    extra = [
        {"title": title, "href": href}
        for title, href in (spec.references if spec is not None else ())
    ]
    if growth.previous_line is None:
        outturn = {"title": spec.outturn.title, "href": spec.outturn.href}
        return [current, outturn, *extra]
    base_year = min(growth.values) - 1
    return [
        current,
        {
            "title": f"OBR EFO {previous_month} {previous_year} (detailed forecast "
            f"tables, receipts, Table {growth.previous_line.table}; "
            f"{fiscal_year_label(base_year)} outturn)",
            "href": build_efo_href(previous_month, previous_year),
        },
        *extra,
    ]


def check_index_stays_positive(path: tuple[str, ...], values: dict) -> None:
    """Compound a rendered series as create_economic_assumption_indices does,
    from 1 in its first listed year, rounding to five decimals.
    An index that rounds to zero would zero the base in every later year, and
    one that overflows would make it infinite."""
    growth = {str(instant): value for instant, value in values.items()}
    index = 1.0
    for year in range(int(min(growth)[:4]) + 1, LAST_INDEX_YEAR + 1):
        in_force = max(instant for instant in growth if instant <= f"{year}-01-01")
        index = round(index * (1 + growth[in_force]), 5)
        if not (math.isfinite(index) and index > 0):
            raise ValueError(
                f"{'.'.join(path)}: the index reaches {index} in {year} at five "
                "decimals, which the model cannot compound from"
            )


def render_receipts_growth_yaml(
    content: str,
    growth: dict[tuple[str, ...], ReceiptsGrowth],
    release: tuple[str, int],
    previous_release: tuple[str, int],
) -> str:
    """Rewrite each receipts series' values and references in a
    yoy_growth.yaml.

    Years before this EFO's first year are kept, so a series' index keeps
    its base year. Years after the OBR's receipts forecast follow
    average_earnings as ``content`` holds it. A series under ``per_capita``
    is written per head of ``ons.population`` as ``content`` holds it, in
    every year to the last that population or the tail states. The result is
    checked to differ from ``content`` only in those values and references.
    """
    before = yaml.safe_load(content)
    expected = copy.deepcopy(before)
    lines = content.split("\n")
    population = None
    for path, series in growth.items():
        if series.spec is not None and series.spec.per_head:
            population = population or population_growth(content)
            series = per_head_growth(series, population)
        tail, tail_comment = receipts_tail(content, series)
        references = receipts_references(series, release, previous_release)

        start, end = _series_block(lines, ("obr", *path))
        indent = 2 * len(path) + 2
        values_start, values_end = _yaml_block(lines, "values", indent, start, end)
        old_values = lines[values_start + 1 : values_end]
        entry_indent = next(
            (_indent(line) for line in old_values if VALUE_LINE_RE.match(line)),
            indent + 2,
        )
        new_values = render_receipts_values(
            old_values,
            entry_indent,
            series,
            tail,
            release,
            previous_release,
            tail_comment,
        )
        lines = [*lines[: values_start + 1], *new_values, *lines[values_end:]]

        start, end = _series_block(lines, ("obr", *path))
        metadata = _yaml_block(lines, "metadata", indent, start, end)
        ref_start, ref_end = _yaml_block(
            lines, "reference", indent + 2, metadata[0], metadata[1]
        )
        pad = " " * (indent + 2)
        new_references = [f"{pad}reference:"] + [
            text
            for reference in references
            for text in (
                f"{pad}  - title: {reference['title']}",
                f"{pad}    href: {reference['href']}",
            )
        ]
        lines = [*lines[:ref_start], *new_references, *lines[ref_end:]]

        node = expected["obr"]
        for key in path:
            node = node[key]
        kept = {
            instant: value
            for instant, value in node["values"].items()
            if int(str(instant)[:4]) < min(series.values)
        }
        node["values"] = {
            **kept,
            **{
                date(year, 1, 1): value
                for year, value in {**series.values, **tail}.items()
            },
        }
        check_index_stays_positive(path, node["values"])
        node["metadata"]["reference"] = references

    rendered = "\n".join(lines)
    if yaml.safe_load(rendered) != expected:
        raise ValueError(
            "Rewriting the receipts growth series changed more than their "
            "values and references"
        )
    return rendered


@dataclass(frozen=True)
class LevelSeriesSpec:
    """A series the OBR publishes as levels across a row of years, not as
    growth down a column.

    ``path`` names the series under ``obr``. The importer finds the table by
    its title, as it finds receipts tables. The OBR gives one unit, ``unit``,
    in the table's header; one row of cells holds consecutive calendar years;
    and one row below it, labelled ``row``, holds a level under each year and
    nowhere else. The importer compares titles, units and labels lowercased,
    without a footnote marker: digits or superscript digits after a letter or
    a closing bracket, as in "National Living Wage (NLW)1". The OBR's note
    says the rate "has been set by the Government up until" a year and that
    "figures beyond" it "are OBR estimates"; the importer labels the years
    on each side of that year, and every such statement in the table must
    name the same calendar year.

    ``anchor`` names the scale whose last bracket's amount the series' index
    uprates. The model projects that amount from its last dated value, and
    its uprating rounds each projected rate to the nearest ``rounding``.
    """

    path: tuple[str, ...]
    title: str
    unit: str
    row: str
    anchor: str
    rounding: float


LEVEL_SERIES_SPECS = (
    LevelSeriesSpec(
        path=("national_living_wage",),
        title="national living wage",
        unit="£ per hour",
        row="national living wage (nlw)",
        # The scale's last bracket holds the national living wage.
        anchor="gov.hmrc.minimum_wage.non_apprentice",
        # gov.hmrc.minimum_wage rounds each projected rate to the nearest penny.
        rounding=0.01,
    ),
)
# A footnote marker ending a level table's title, unit or label.
LEVEL_FOOTNOTE_RE = re.compile(
    r"(?<=[a-z)\]])(?:\d+|[\u2070\u00b9\u00b2\u00b3\u2074-\u2079]+)$", re.IGNORECASE
)
# A statement of the year the government has set the rate up until, with any
# negation before it and the whole token after it, and a range such as
# "2027 - 28" with its spaces.
SET_BY_GOVERNMENT_RE = re.compile(
    r"(?:\b(not|never)\s+(?:yet\s+)?(?:been\s+)?)?"
    r"set by the government up until (\S+(?:\s*[-\u2013\u2014]\s*\S+)?)"
)
OBR_ESTIMATES_RE = re.compile(r"figures beyond (\d{4}) are obr estimates")


@dataclass(frozen=True)
class LevelLine:
    """A level series as the OBR publishes it in one EFO: levels by calendar
    year, and the last year whose rate the government has set."""

    table: str
    label: str
    levels: dict[int, float]
    set_until: int


@dataclass(frozen=True)
class LevelGrowth:
    """Growth in a level series, by year, to six decimals, from the table's
    second year to its last. compute_level_growth writes each year's level
    over the year before's; penny_preserving_growth then changes the growth
    in any year after the anchor's that would project another penny."""

    values: dict[int, float]
    line: LevelLine
    spec: LevelSeriesSpec


@dataclass(frozen=True)
class LevelAnchor:
    """The rate the model projects a level series' parameter from: that
    parameter's last dated value, the date it takes effect, and the
    parameter's uprating metadata. policyengine-core's uprate_parameters
    projects each later rate from this value."""

    instant: date
    rate: float
    uprating: dict


def level_label(value: str | None) -> str:
    """Return a level table's title, unit or label as the importer compares
    it: lowercased, with single spaces and without a footnote marker."""
    return LEVEL_FOOTNOTE_RE.sub("", normalise_label(value))


def _year_columns(row: dict[str, str | None]) -> dict[str, int]:
    """Return a row's columns and years, if every non-empty cell holds a
    year."""
    cells = {
        column: str(value).strip()
        for column, value in row.items()
        if str(value or "").strip()
    }
    if cells and all(YEAR_RE.match(text) for text in cells.values()):
        return {column: int(text) for column, text in cells.items()}
    return {}


def _set_until(rows: list[dict[str, str | None]], where: str) -> int:
    """Read the last year the government has set from the OBR's note. Every
    statement in the table of the year the government has set the rate up
    until, or of the year beyond which figures are OBR estimates, must name
    the same calendar year, and none may deny it."""
    texts = [normalise_label(value) for row in rows for value in row.values()]
    notes = [text for text in texts if SET_BY_GOVERNMENT_RE.search(text)]
    if len(notes) != 1:
        raise ValueError(
            f"The importer needs one note in {where} saying which years the "
            f"government has set and which the OBR estimates; found {len(notes)}"
        )
    statements = [
        (negation, token.rstrip(".,;:)"))
        for negation, token in SET_BY_GOVERNMENT_RE.findall(notes[0])
    ]
    for negation, token in statements:
        if negation:
            raise ValueError(
                f"The OBR's note in {where} says the rate has {negation} been "
                f"set by the government up until a year, so it names no year "
                f"the government has set: {notes[0]!r}"
            )
        if not re.fullmatch(r"\d{4}", token):
            raise ValueError(
                f"The OBR's note in {where} gives {token!r}, not one calendar "
                f"year, as the year the government has set the rate up until: "
                f"{notes[0]!r}"
            )
    set_years = sorted({int(token) for _, token in statements})
    if len(set_years) != 1:
        raise ValueError(
            f"The OBR's note in {where} names more than one year the "
            f"government has set the rate up until, {set_years}: {notes[0]!r}"
        )
    set_until = set_years[0]
    estimates = sorted(
        {int(year) for text in texts for year in OBR_ESTIMATES_RE.findall(text)}
    )
    if estimates != [set_until]:
        raise ValueError(
            f"The importer found no statement in {where} that the figures "
            f"beyond {set_until}, and no others, are OBR estimates; the OBR "
            f"names {estimates or 'no year'}: {notes[0]!r}"
        )
    return set_until


def find_level_line(
    sheets: dict[str, list[dict[str, str | None]]], spec: LevelSeriesSpec
) -> LevelLine:
    """Read the levels in the one row labelled ``spec.row`` of the one table
    titled ``spec.title``, across its row of years.

    It refuses any other layout rather than read it: another unit, a second
    row of years or of the label, a level missing under a year or one with
    no year above it, or years that skip or repeat.
    """
    name = ".".join(spec.path)
    tables = [
        (table, sheet, table_rows)
        for sheet, rows in sheets.items()
        for table, title, table_rows in sheet_tables(rows)
        if level_label(title) == spec.title
    ]
    if len(tables) != 1:
        found = ", ".join(f"sheet {sheet}" for _, sheet, _ in tables) or "none"
        raise ValueError(f'Expected one "{spec.title}" table for {name}; found {found}')
    table, sheet, rows = tables[0]
    where = f"Table {table} (sheet {sheet})"
    year_rows = [index for index, row in enumerate(rows) if _year_columns(row)]
    if len(year_rows) != 1:
        raise ValueError(
            "The importer needs one row of years across the columns of "
            f"{where}; found {len(year_rows)}"
        )
    header = year_rows[0]
    years = _year_columns(rows[header])
    first_year_column = min(column_index(column) for column in years)
    matches = []
    for index, row in enumerate(rows):
        labels = [
            value
            for column, value in sorted(
                row.items(), key=lambda item: column_index(item[0])
            )
            if column_index(column) < first_year_column and normalise_label(value)
        ]
        if labels and level_label(labels[0]) == spec.row:
            matches.append((index, labels[0], row))
    if len(matches) != 1:
        raise ValueError(
            f'Expected one "{spec.row}" row in {where} for {name}; found {len(matches)}'
        )
    index, label, row = matches[0]
    if index < header:
        raise ValueError(f'{where} has its "{spec.row}" row above its years')
    units = [
        level_label(value)
        for header_row in rows[:header]
        for value in header_row.values()
        if level_label(value)
    ]
    if units != [spec.unit]:
        raise ValueError(
            f"The importer needs the unit {spec.unit!r}, and no other, above the "
            f"years in {where}; found {units}"
        )
    ordered = [years[column] for column in sorted(years, key=column_index)]
    if ordered != list(range(ordered[0], ordered[0] + len(ordered))):
        raise ValueError(f"{where}'s years skip, repeat or run backwards: {ordered}")
    stray = sorted(
        column
        for column, value in row.items()
        if column_index(column) >= first_year_column
        and column not in years
        and str(value or "").strip()
    )
    if stray:
        raise ValueError(f"{where} has {name} values with no year above them: {stray}")
    levels = {}
    for column, year in years.items():
        text = row.get(column)
        try:
            level = float(text)
        except (TypeError, ValueError):
            level = None
        if level is None or not math.isfinite(level) or level <= 0:
            raise ValueError(f"{where} has no positive {year} {name} level: {text!r}")
        levels[year] = level
    set_until = _set_until(rows, where)
    if not min(levels) <= set_until <= max(levels):
        raise ValueError(
            f"The OBR's note in {where} says the government has set the rate up "
            f"until {set_until}, outside the table's years "
            f"{min(levels)}-{max(levels)}"
        )
    if TABLE_NUMBER_RE.fullmatch(sheet):
        table = sheet
    return LevelLine(
        table=table,
        label=LEVEL_FOOTNOTE_RE.sub("", " ".join(str(label).split())),
        levels=dict(sorted(levels.items())),
        set_until=set_until,
    )


def compute_level_growth(
    xlsx_bytes: bytes, specs: tuple[LevelSeriesSpec, ...] = LEVEL_SERIES_SPECS
) -> dict[tuple[str, ...], LevelGrowth]:
    """Read the growth in each level series from an EFO's economy tables:
    each year's level over the year before's, less one, to six decimals."""
    sheets = read_workbook_sheets(xlsx_bytes)
    result = {}
    for spec in specs:
        name = ".".join(spec.path)
        line = find_level_line(sheets, spec)
        values = {
            year: round(line.levels[year] / line.levels[year - 1] - 1, 6) + 0.0
            for year in sorted(line.levels)[1:]
        }
        for year, value in values.items():
            if not math.isfinite(value):
                raise ValueError(
                    f"{name}: the {year} level over the {year - 1} level gives "
                    f"growth of {value}, which the importer cannot write"
                )
        result[spec.path] = LevelGrowth(values, line, spec)
    return result


def dated_values(name: str, values: dict) -> dict[date, float]:
    """Return a parameter's values by the day each takes effect.
    policyengine-core's Parameter reads ``values`` (keys as text, as core's
    YAML loader gives them) and drops any value marked expected; each key
    then becomes the day core's instant() reads from it, so 2028-04-01,
    quoted or not, and 2028-04 both name 1 April 2028. It refuses two keys
    that name the same day."""
    from policyengine_core.parameters import Parameter
    from policyengine_core.periods import instant

    dated = {}
    for entry in Parameter(name, {"values": values}).values_list:
        day = instant(entry.instant_str).date
        if day in dated:
            raise ValueError(f"{name} dates two values on {day}")
        dated[day] = entry.value
    return dated


def read_level_anchor(spec: LevelSeriesSpec) -> LevelAnchor:
    """Read the last dated value of ``spec.anchor``'s last bracket's amount,
    and its uprating metadata, from its file in the model's parameter tree.
    It loads the file with policyengine-core's YAML loader, which refuses a
    key the file repeats, and takes the latest day dated_values reads, so
    it anchors where core does. It refuses an amount that the series' index
    does not uprate to the nearest ``spec.rounding``."""
    from policyengine_core.parameters import config

    path = (
        get_repo_root() / "policyengine_uk/parameters" / Path(*spec.anchor.split("."))
    )
    amount = yaml.load(path.with_suffix(".yaml").read_text(), Loader=config.Loader)[
        "brackets"
    ][-1]["amount"]
    uprating = amount["metadata"]["uprating"]
    expected = {
        "parameter": "gov.economic_assumptions.indices.obr." + ".".join(spec.path),
        "rounding": {"type": "nearest", "interval": spec.rounding},
    }
    if uprating != expected:
        raise ValueError(
            f"{spec.anchor}'s last bracket must uprate by {expected['parameter']} "
            f"to the nearest {spec.rounding}; its metadata gives {uprating}"
        )
    values = dated_values(f"{spec.anchor}'s last bracket", amount["values"])
    instant = max(values)
    return LevelAnchor(instant=instant, rate=float(values[instant]), uprating=uprating)


def compound_model_index(values: dict, last_year: int) -> dict[int, float]:
    """Compound a growth series' index as create_economic_assumption_indices
    does, to ``last_year``: 1 in the series' first listed year, then each
    year's index times one plus the growth in force on 1 January, rounded to
    five decimals. The builder decides where an index ends (see
    check_level_index_in_model)."""
    growth = {str(instant): value for instant, value in values.items()}
    first = int(min(growth)[:4])
    index = {first: 1.0}
    for year in range(first + 1, last_year + 1):
        in_force = max(instant for instant in growth if instant <= f"{year}-01-01")
        index[year] = round(index[year - 1] * (1 + growth[in_force]), 5)
    return index


def nearest_units(amount: float, rounding: float) -> float:
    """Return ``amount`` as a whole number of ``rounding``, as
    uprate_parameters (policyengine-core) rounds a projected rate to the
    nearest interval: it divides by the interval first and rounds the
    quotient with Python's round(), which takes a half to the even number.
    £13.525 over £0.01 gives exactly 1,352.5 as a float, so £13.525 becomes
    1,352 pennies. Infinity if the division overflows."""
    units = amount / rounding
    return round(units) if math.isfinite(units) else math.inf


def level_text(level: float, rounding: float) -> str:
    """Write ``level`` to the nearest ``rounding`` as the model rounds it
    (nearest_units), with the interval's decimal places: "13.52" for
    £13.525. If the division overflows, it formats the level itself to
    those places."""
    places = max(0, -Decimal(repr(rounding)).as_tuple().exponent)
    units = nearest_units(level, rounding)
    return f"{units * rounding if math.isfinite(units) else level:.{places}f}"


def projected_rate_units(
    index: dict[int, float], start: int, rate: float, year: int, rounding: float
) -> float:
    """Return the rate uprate_parameters (policyengine-core) projects for
    ``year`` from ``rate``, in force in ``start``, as a whole number of
    ``rounding``: the rate times the index's growth since, rounded to the
    nearest ``rounding`` (nearest_units). Infinity if that overflows."""
    return nearest_units(rate * (index[year] / index[start]), rounding)


def _level_growth_series(series: LevelGrowth, kept: dict) -> dict[str, float]:
    """Return the growth the model reads for a level series, keyed by date:
    the years the file keeps before the table, then the table's."""
    growth = {str(instant): value for instant, value in kept.items()}
    growth.update({f"{year}-01-01": value for year, value in series.values.items()})
    return growth


def check_level_index(path: tuple[str, ...], series: LevelGrowth, kept: dict) -> None:
    """Refuse a table whose growth takes the model's index to zero or
    infinity. The model compounds ``kept``, the years the file keeps before
    the table, and then the table's growth (compound_model_index), so the
    importer compounds the same series."""
    index = compound_model_index(_level_growth_series(series, kept), max(series.values))
    for year, value in sorted(series.values.items()):
        if not (math.isfinite(index[year]) and index[year] > 0):
            raise ValueError(
                f"{'.'.join(path)}: {year} growth of {value} takes the index to "
                f"{index[year]} at five decimals, which the model cannot "
                "compound from"
            )


def penny_preserving_growth(
    path: tuple[str, ...], series: LevelGrowth, kept: dict, anchor: LevelAnchor
) -> LevelGrowth:
    """Choose the growth in each table year after ``anchor``'s so that the
    model projects the table's level, both rounded to the nearest
    ``series.spec.rounding``.

    The model compounds ``kept``, the earlier years the file keeps, and then
    ``series`` into an index (compound_model_index), and projects each later
    rate from the anchor's rate (projected_rate_units). The importer refuses
    a table whose level in the anchor's year differs from the anchor's rate
    at that rounding, and one whose index starts after the anchor's year.
    Where the OBR publishes the table's first level for a year after the
    anchor's, the importer has no ratio into that year: the model carries
    the anchor's rate there through the growth the importer keeps
    (``kept``), and the importer refuses the table if that projection rounds
    to another level than the OBR's. Each later year keeps its growth if the
    projection rounds to the table's level. Otherwise the importer takes the
    growth, to six decimals, from the level the index carries the rate to in
    the year before to the table's level, or else the nearest six-decimal
    growth to that which does round to the table's level. It refuses a year
    that no six-decimal growth can reproduce.
    """
    name = ".".join(path)
    line = series.line
    rounding = series.spec.rounding
    start, rate, last = anchor.instant.year, anchor.rate, max(line.levels)
    if start in line.levels and nearest_units(
        line.levels[start], rounding
    ) != nearest_units(rate, rounding):
        raise ValueError(
            f"{name}: the OBR's {start} level, {line.levels[start]!r}, differs "
            f"to the nearest {rounding} from {rate!r}, the rate "
            f"{series.spec.anchor} holds from {anchor.instant}"
        )
    values = dict(series.values)
    growth = _level_growth_series(series, kept)
    first = int(min(growth)[:4])
    if start < first:
        raise ValueError(
            f"{name}: the index starts in {first}, after {start}, the year of "
            f"the last rate {series.spec.anchor} holds, so the model cannot "
            "project from it"
        )
    for year in [year for year in sorted(line.levels) if year > start]:
        index = compound_model_index(growth, last)
        for base in (start, year - 1):
            if not (math.isfinite(index[base]) and index[base] > 0):
                raise ValueError(
                    f"{name}: the index reaches {index[base]} in {base}, so the "
                    f"model cannot project the {year} level"
                )
        refusal = ValueError(
            f"{name}: no {year} growth to six decimals lets the model project "
            f"the OBR's {year} level, {line.levels[year]!r}, from the {start} "
            f"rate to the nearest {rounding}"
        )
        if not math.isfinite(line.levels[year] / rounding):
            raise refusal
        target = nearest_units(line.levels[year], rounding)
        if year not in values:
            projected = projected_rate_units(index, start, rate, year, rounding)
            if projected != target:
                raise ValueError(
                    f"{name}: the OBR publishes Table {line.table} from {year}, "
                    f"after {start}, the year of the last rate "
                    f"{series.spec.anchor} holds: {rate!r} from "
                    f"{anchor.instant}. The model carries that rate to {year} "
                    "through the growth the importer keeps and projects "
                    f"{level_text(projected * rounding, rounding)}, but the OBR "
                    f"publishes {line.levels[year]!r}, which rounds to "
                    f"{level_text(line.levels[year], rounding)} to the nearest "
                    f"{rounding}"
                )
            continue

        def units(micros: int) -> float:
            try:
                value = micros / 1_000_000
            except OverflowError:
                return math.inf
            trial = compound_model_index({**growth, f"{year}-01-01": value}, last)
            return projected_rate_units(trial, start, rate, year, rounding)

        written = round(Decimal(repr(values[year])) * 1_000_000)
        if units(written) == target:
            continue

        def first_above(bound: float) -> int:
            """The least whole number of millionths, from -1 million (growth
            of -100%), whose projection exceeds ``bound``. The projection
            never falls as the growth rises, so a bisection finds it."""
            low, high = -1_000_000, max(written, 1)
            if units(low) > bound:
                return low
            while units(high) <= bound:
                low, high = high, 2 * high
            while high - low > 1:
                middle = (low + high) // 2
                if units(middle) > bound:
                    high = middle
                else:
                    low = middle
            return high

        lowest, highest = first_above(target - 1), first_above(target) - 1
        if lowest > highest:
            raise refusal
        carried = rate * (index[year - 1] / index[start])
        ratio = line.levels[year] / carried - 1
        sequential = round(ratio * 1e6) if math.isfinite(ratio * 1e6) else lowest
        values[year] = min(max(sequential, lowest), highest) / 1_000_000 + 0.0
        growth[f"{year}-01-01"] = values[year]
    return replace(series, values=values)


def _kept_level_values(obr: dict, path: tuple[str, ...], series: LevelGrowth) -> dict:
    """Return the values a yoy_growth.yaml's ``obr`` mapping holds for a
    level series before its table's second year, which a render keeps."""
    node = obr
    for key in path:
        node = node[key]
    return {
        instant: value
        for instant, value in node["values"].items()
        if int(str(instant)[:4]) < min(series.values)
    }


def _level_anchor(
    path: tuple[str, ...],
    series: LevelGrowth,
    anchors: dict[tuple[str, ...], LevelAnchor] | None,
) -> LevelAnchor:
    """Return ``anchors[path]`` if given, or else the anchor
    read_level_anchor reads from the series' parameter file."""
    return anchors[path] if anchors is not None else read_level_anchor(series.spec)


def penny_preserving_level_growth(
    content: str,
    growth: dict[tuple[str, ...], LevelGrowth],
    anchors: dict[tuple[str, ...], LevelAnchor] | None = None,
) -> dict[tuple[str, ...], LevelGrowth]:
    """Run penny_preserving_growth on each level series, given the years
    before its table that ``content``, a yoy_growth.yaml, keeps, and its
    anchor (``anchors``, or by default read_level_anchor)."""
    obr = yaml.safe_load(content)["obr"]
    return {
        path: penny_preserving_growth(
            path,
            series,
            _kept_level_values(obr, path, series),
            _level_anchor(path, series, anchors),
        )
        for path, series in growth.items()
    }


def build_model_index(content: str, path: tuple[str, ...]) -> dict[int, float]:
    """Build, by year, the index the model compounds from ``obr.<path>`` when
    it reads ``content`` as its yoy_growth.yaml.

    process_parameter_tree runs its generation steps on the parameters the
    YAML files hold. This runs those steps, up to and including
    create_economic_assumption_indices, on the same parameters with
    ``content``'s growth series in place of the file's, and reads the index
    that builder writes. The steps before it add growth series of their own,
    and the builder decides where each index ends.
    """
    from policyengine_core.parameters import ParameterNode, config

    from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
        create_economic_assumption_indices,
    )
    from policyengine_uk.tax_benefit_system import (
        GENERATION_STEPS,
        statutory_parameters,
    )

    parameters = statutory_parameters()
    assumptions = parameters.gov.economic_assumptions
    del assumptions.children["yoy_growth"]
    assumptions.add_child(
        "yoy_growth",
        ParameterNode(
            "gov.economic_assumptions.yoy_growth",
            data=yaml.load(content, Loader=config.Loader),
        ),
    )
    for step in GENERATION_STEPS:
        parameters = step(parameters)
        if step is create_economic_assumption_indices:
            break
    index = parameters.get_child(
        "gov.economic_assumptions.indices.obr." + ".".join(path)
    )
    return {
        int(entry.instant_str[:4]): entry.value
        for entry in sorted(index.values_list, key=lambda entry: entry.instant_str)
    }


def check_level_index_in_model(
    content: str,
    path: tuple[str, ...],
    series: LevelGrowth,
    build_index=None,
) -> None:
    """Check the index the model builds from ``content``'s ``obr.<path>``
    against the importer's. ``build_index(content, path)`` builds it; by
    default build_model_index does, as the model does. The index must reach
    the table's last year, and compound_model_index must compound the same
    index from the written series in every year the model's has."""
    name = ".".join(path)
    model = (build_index or build_model_index)(content, path)
    last = max(series.line.levels)
    if max(model) < last:
        raise ValueError(
            f"{name}: the model's index ends in {max(model)}, so it cannot "
            f"project the {last} level"
        )
    node = yaml.safe_load(content)["obr"]
    for key in path:
        node = node[key]
    importer = compound_model_index(node["values"], max(model))
    differ = sorted(
        year
        for year in model.keys() | importer.keys()
        if model.get(year) != importer.get(year)
    )
    if differ:
        raise ValueError(
            f"{name}: compound_model_index and the model's index differ in "
            f"{differ}, so the importer cannot check the model's pennies"
        )


def average_earnings_years(content: str, after_year: int) -> dict[int, float]:
    """Return ``average_earnings`` after ``after_year``, year for year: the
    path ``average_earnings_path`` gives, with an entry in every year
    average_earnings has one, so the two series list the same years."""
    values = yaml.safe_load(content)["obr"]["average_earnings"]["values"]
    later = {
        int(str(instant)[:4]): float(value)
        for instant, value in values.items()
        if int(str(instant)[:4]) > after_year
    }
    return dict(sorted({**average_earnings_path(content, after_year), **later}.items()))


def render_level_values(
    old_lines: list[str],
    indent: int,
    growth: LevelGrowth,
    tail: dict[int, float],
    release: tuple[str, int],
) -> list[str]:
    """Render a level series' values entries: the earlier years it keeps,
    then the growth into the rates the government has set, then into the
    OBR's estimates, then the average_earnings path."""
    first_year = min(growth.values)
    kept: list[str] = []
    pending: list[str] = []
    for line in old_lines:
        match = VALUE_LINE_RE.match(line)
        if match is None:
            if line.strip() and not line.strip().startswith("#"):
                raise ValueError(f"Unexpected line in a values block: {line!r}")
            pending.append(line)
            continue
        if int(match.group(1)) < first_year:
            kept += pending + [line]
        pending = []

    month, year = release
    published = growth.line
    pad = " " * indent
    lines = list(kept)
    source = (
        f'OBR EFO {month} {year}, economy Table {published.table} "{published.label}"'
    )
    for kind, years in (
        (
            "The government set the rates for",
            [y for y in growth.values if y <= published.set_until],
        ),
        (
            "The OBR estimates the rates for",
            [y for y in growth.values if y > published.set_until],
        ),
    ):
        if not years:
            continue
        span = f"{years[0]}" if len(years) == 1 else f"{years[0]}-{years[-1]}"
        start, end = years[0] - 1, years[-1]
        lines.append(
            f"{pad}# {kind} {span}: £{published.levels[start]:.2f} in {start} "
            f"to £{published.levels[end]:.2f} in {end} ({source})"
        )
        lines += [f"{pad}{y}-01-01: {format_growth(growth.values[y])}" for y in years]
    lines.append(
        f"{pad}# After the OBR forecast, the importer copies average_earnings "
        "year for year"
    )
    lines += [f"{pad}{y}-01-01: {format_growth(v)}" for y, v in tail.items()]
    return lines


def render_level_series_yaml(
    content: str,
    growth: dict[tuple[str, ...], LevelGrowth],
    release: tuple[str, int],
    anchors: dict[tuple[str, ...], LevelAnchor] | None = None,
    build_index=None,
) -> str:
    """Rewrite each level series' values and first reference in a
    yoy_growth.yaml.

    It keeps the years before the table's second year, so the series' index
    keeps its base year, and the series' other references. It refuses a
    table whose growth takes the index to zero (check_level_index), and
    writes the growth penny_preserving_growth chooses from each series'
    anchor (``anchors``, or by default read_level_anchor), so the model
    projects each table level after the anchor's year to the table's penny.
    Years after the table follow average_earnings as ``content`` holds it.
    It checks that the finished series' index stays above zero, that the
    result differs from ``content`` only in those values and that reference,
    and that the index the model builds from the result
    (check_level_index_in_model, with ``build_index``) matches the
    importer's.
    """
    month, year = release
    expected = copy.deepcopy(yaml.safe_load(content))
    lines = content.split("\n")
    written = []
    for path, series in growth.items():
        node = expected["obr"]
        for key in path:
            node = node[key]
        kept = _kept_level_values(expected["obr"], path, series)
        check_level_index(path, series, kept)
        series = penny_preserving_growth(
            path, series, kept, _level_anchor(path, series, anchors)
        )
        tail = average_earnings_years(content, max(series.values))
        start, end = _series_block(lines, ("obr", *path))
        indent = 2 * len(path) + 2
        values_start, values_end = _yaml_block(lines, "values", indent, start, end)
        old_values = lines[values_start + 1 : values_end]
        entry_indent = next(
            (_indent(line) for line in old_values if VALUE_LINE_RE.match(line)),
            indent + 2,
        )
        new_values = render_level_values(
            old_values, entry_indent, series, tail, release
        )
        lines = [*lines[: values_start + 1], *new_values, *lines[values_end:]]

        start, end = _series_block(lines, ("obr", *path))
        metadata = _yaml_block(lines, "metadata", indent, start, end)
        ref_start, ref_end = _yaml_block(
            lines, "reference", indent + 2, metadata[0], metadata[1]
        )
        pad = " " * (indent + 2)
        title = next(
            (
                index
                for index in range(ref_start + 1, ref_end)
                if lines[index].startswith(f"{pad}  - title: ")
            ),
            None,
        )
        if title is None or not lines[title + 1].startswith(f"{pad}    href: "):
            raise ValueError(f"Could not find the first reference of {'.'.join(path)}")
        reference = {
            "title": build_reference_title(month, year, series.line.table),
            "href": build_efo_href(month, year),
        }
        lines[title] = f"{pad}  - title: {reference['title']}"
        lines[title + 1] = f"{pad}    href: {reference['href']}"

        node["values"] = {
            **kept,
            **{
                date(entry_year, 1, 1): value
                for entry_year, value in {**series.values, **tail}.items()
            },
        }
        check_index_stays_positive(path, node["values"])
        node["metadata"]["reference"][0] = reference
        written.append((path, series))

    rendered = "\n".join(lines)
    if yaml.safe_load(rendered) != expected:
        raise ValueError(
            "Rewriting the level series changed more than their values and "
            "first reference"
        )
    for path, series in written:
        check_level_index_in_model(rendered, path, series, build_index)
    return rendered


def infer_workbook_release(xlsx_bytes: bytes) -> tuple[str, int] | None:
    """The release a detailed forecast tables workbook names on its contents
    sheet, e.g. "March 2026 Economic and fiscal outlook - detailed forecast
    tables", or None."""
    with ZipFile(BytesIO(xlsx_bytes)) as archive:
        sheet_names = list(_sheet_paths(archive))
    contents = next((s for s in sheet_names if s.lower() == "contents"), None)
    if contents is None:
        return None
    for row in read_sheet_rows(xlsx_bytes, contents)[:5]:
        for value in row.values():
            text = str(value or "")
            match = MONTH_RE.search(text)
            if match and "outlook" in text.lower():
                return match.group(1).capitalize(), int(match.group(2))
    return None


def resolve_release(xlsx_bytes: bytes, source_name: str) -> tuple[str, int] | None:
    """A workbook's release from its contents sheet, else from its name."""
    release = infer_workbook_release(xlsx_bytes)
    if release is not None:
        return release
    try:
        return infer_release(source_name)
    except ValueError:
        return None


def release_order(release: tuple[str, int]) -> tuple[int, int]:
    month, year = release
    return year, MONTHS.index(month.lower())


def infer_release(source_name: str) -> tuple[str, int]:
    """The release a file name or URL names, e.g. "receipts_march_2026.xlsx"
    or ".../March%202026%20EFO.xlsx"."""
    match = MONTH_RE.search(unquote(source_name))
    if not match:
        raise ValueError(
            "Could not infer the OBR release month/year from the source name. "
            "Pass --release-month and --release-year."
        )
    month = match.group(1).capitalize()
    year = int(match.group(2))
    return month, year


def infer_forecast_start_year(month: str, year: int) -> int:
    if month.lower() == "march":
        return year - 1
    return year


def build_efo_href(month: str, year: int) -> str:
    return f"https://obr.uk/efo/economic-and-fiscal-outlook-{month.lower()}-{year}/"


def build_reference_title(month: str, year: int, table: str) -> str:
    return f"OBR EFO {month} {year} (detailed forecast tables, economy, Table {table})"


def replace_year_value(section: str, year: int, value: float) -> str:
    pattern = re.compile(
        rf"(^      {year}-01-01:\s*).*$",
        flags=re.MULTILINE,
    )
    replacement = rf"\g<1>{value:.4f}"
    updated, count = pattern.subn(replacement, section, count=1)
    if count == 0:
        raise ValueError(f"Could not find year {year} in section")
    return updated


def replace_first_reference(section: str, title: str, href: str) -> str:
    title_pattern = re.compile(r"(^        - title:\s*).*$", flags=re.MULTILINE)
    href_pattern = re.compile(r"(^          href:\s*).*$", flags=re.MULTILINE)

    updated, title_count = title_pattern.subn(rf"\g<1>{title}", section, count=1)
    if title_count == 0:
        raise ValueError("Could not find reference title in section")

    updated, href_count = href_pattern.subn(rf"\g<1>{href}", updated, count=1)
    if href_count == 0:
        raise ValueError("Could not find reference href in section")
    return updated


def replace_series_section(content: str, series_key: str, updated_section: str) -> str:
    pattern = re.compile(
        rf"(^  {series_key}:\n.*?)(?=^  [a-z_]+:|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    updated, count = pattern.subn(updated_section, content, count=1)
    if count == 0:
        raise ValueError(f"Could not find section for {series_key}")
    return updated


def update_yoy_growth_yaml(
    yaml_path: Path,
    series_values: dict[str, dict[int, float]],
    month: str,
    year: int,
    forecast_start_year: int,
    forecast_years: int,
) -> None:
    yaml_path.write_text(
        render_yoy_growth_yaml(
            yaml_path.read_text(),
            series_values,
            month,
            year,
            forecast_start_year,
            forecast_years,
        )
    )


def render_yoy_growth_yaml(
    content: str,
    series_values: dict[str, dict[int, float]],
    month: str,
    year: int,
    forecast_start_year: int,
    forecast_years: int,
) -> str:
    yaml.safe_load(content)
    forecast_end_year = forecast_start_year + forecast_years - 1
    href = build_efo_href(month, year)

    for spec in SERIES_SPECS:
        section_pattern = re.compile(
            rf"(^  {spec.key}:\n.*?)(?=^  [a-z_]+:|\Z)",
            flags=re.MULTILINE | re.DOTALL,
        )
        match = section_pattern.search(content)
        if not match:
            raise ValueError(f"Could not find section for {spec.key}")
        section = match.group(1)

        available_years = [
            target_year
            for target_year in range(forecast_start_year, forecast_end_year + 1)
            if target_year in series_values[spec.key]
        ]
        if not available_years:
            raise ValueError(
                f"No {spec.key} values found for {forecast_start_year}-{forecast_end_year}"
            )

        for target_year in available_years:
            try:
                section = replace_year_value(
                    section, target_year, series_values[spec.key][target_year]
                )
            except ValueError:
                # Only existing entries are replaced: an entry added here
                # would also move every later year up to the next entry.
                raise ValueError(
                    f"{spec.key} has no {target_year}-01-01 entry for this EFO's "
                    f"{target_year} forecast. Add one, with the long-run path "
                    "after it recomputed (see the README's steps for a new EFO), "
                    "then rerun"
                ) from None

        section = replace_first_reference(
            section,
            build_reference_title(month, year, spec.table),
            href,
        )
        content = replace_series_section(content, spec.key, section)

    yaml.safe_load(content)
    return content


def print_summary(
    series_values: dict[str, dict[int, float]],
    forecast_start_year: int,
    forecast_years: int,
) -> None:
    forecast_end_year = forecast_start_year + forecast_years - 1
    print(
        f"Updating forecast years {forecast_start_year}-{forecast_end_year} "
        f"for {len(SERIES_SPECS)} OBR economy series"
    )
    for spec in SERIES_SPECS:
        values = series_values[spec.key]
        window = [
            f"{year}: {values[year]:.4f}"
            for year in range(forecast_start_year, forecast_end_year + 1)
            if year in values
        ]
        print(f"- {spec.key}: {', '.join(window)}")


def print_receipts_summary(
    growth: dict[tuple[str, ...], ReceiptsGrowth],
    population: dict[int, float] | None = None,
) -> None:
    """Print each series' growth: a series under ``per_capita`` per head when
    ``population`` is given, as it is written."""
    print(f"Updating {len(growth)} OBR receipts growth series")
    for path, series in growth.items():
        basis = ""
        if series.spec is not None and series.spec.per_head:
            if population is None:
                basis = ", aggregate"
            else:
                series = per_head_growth(series, population)
                basis = ", per head"
        window = ", ".join(
            f"{year}: {format_growth(value)}"
            for year, value in sorted(series.values.items())
        )
        print(f"- {'.'.join(path)} (Table {series.line.table}{basis}): {window}")


def print_level_summary(growth: dict[tuple[str, ...], LevelGrowth]) -> None:
    print(f"The importer reads {len(growth)} OBR level series")
    for path, series in growth.items():
        levels = series.line.levels
        window = ", ".join(
            f"{year}: {format_growth(value)}"
            + (
                ""
                if value == round(levels[year] / levels[year - 1] - 1, 6) + 0.0
                else " (the importer moves it off the levels' ratio, which "
                "projects another penny)"
            )
            for year, value in sorted(series.values.items())
        )
        print(
            f"- {'.'.join(path)} (Table {series.line.table}; the government "
            f"has set rates up until {series.line.set_until}): {window}"
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import OBR economy forecast tables into yoy_growth.yaml.",
    )
    parser.add_argument("--url", help="OBR ZIP/XLSX download URL")
    parser.add_argument("--file", help="Local ZIP/XLSX file path")
    parser.add_argument(
        "--yaml-path",
        type=Path,
        default=None,
        help="Override the target yoy_growth.yaml path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write to a separate output file instead of updating yoy_growth.yaml in place",
    )
    parser.add_argument(
        "--release-month",
        help="Override the inferred OBR release month (e.g. March)",
    )
    parser.add_argument(
        "--release-year",
        type=int,
        help="Override the inferred OBR release year (e.g. 2026)",
    )
    parser.add_argument(
        "--forecast-start-year",
        type=int,
        help="Override the first year to update in yoy_growth.yaml",
    )
    parser.add_argument(
        "--forecast-years",
        type=int,
        default=6,
        help="Number of forecast years to update (default: 6)",
    )
    parser.add_argument(
        "--receipts-url",
        help=(
            "OBR receipts detailed forecast tables (XLSX), for September CPI; "
            "without it the September CPI gap uses Q3 CPI"
        ),
    )
    parser.add_argument("--receipts-file", help="Local receipts XLSX file path")
    parser.add_argument(
        "--previous-receipts-url",
        help=(
            "Receipts detailed forecast tables (XLSX) from the EFO whose outturn "
            "year is the year before this one's (March 2025 for March 2026), "
            "the base for the receipts growth series' first year"
        ),
    )
    parser.add_argument(
        "--previous-receipts-file", help="Local previous receipts XLSX file path"
    )
    parser.add_argument(
        "--skip-receipts-growth",
        action="store_true",
        help=(
            "Do not update the receipts growth series (stamp_duty_land_tax, "
            "business_rates) that project corporate SDLT and business rates, "
            "or the gambling_duty_bases series that project the gambling "
            "duty inputs"
        ),
    )
    parser.add_argument(
        "--skip-national-living-wage",
        action="store_true",
        help=(
            "Do not update national_living_wage, which projects the minimum "
            "wage rates, from the economy tables' national living wage table "
            "(Table 1.13 in October 2026)"
        ),
    )
    parser.add_argument(
        "--gaps-only",
        action="store_true",
        help=(
            "Leave yoy_growth.yaml as it is and regenerate the forecast gaps "
            "against the calendar-year growth it holds"
        ),
    )
    parser.add_argument(
        "--skip-statutory-gaps",
        action="store_true",
        help=(
            "Do not update the statutory uprating input forecast gaps "
            "(September CPI, May-July earnings)"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the extracted values without updating yoy_growth.yaml",
    )
    return parser


def write_all_or_none(outputs: dict[Path, str]) -> None:
    """Write every file or leave all of them as they were.

    Each new file is staged beside its target and each existing target is
    copied to a backup beside it before anything moves. Targets are then
    replaced by atomic moves. On any failure, each replaced target is put
    back by an atomic move from its backup, which never truncates it, so a
    second failure cannot leave a file empty. If a restore fails, its backup
    is kept and named in the error. Growth and gaps never mix forecasts
    silently.
    """
    staged: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    replaced: list[Path] = []
    keep: set[Path] = set()
    try:
        for path, content in outputs.items():
            staging = path.with_name(f".{path.name}.staged")
            staging.write_text(content)
            staged[path] = staging
        for path in outputs:
            if path.exists():
                backup = path.with_name(f".{path.name}.backup")
                shutil.copy2(path, backup)
                backups[path] = backup
        for path, staging in staged.items():
            os.replace(staging, path)
            replaced.append(path)
    except BaseException as error:
        unrestored = []
        for path in replaced:
            try:
                if path in backups:
                    os.replace(backups[path], path)
                else:
                    path.unlink()
            except OSError:
                unrestored.append(path)
        if unrestored:
            keep = {backups[path] for path in unrestored if path in backups}
            raise OSError(
                "Could not restore "
                + ", ".join(str(path) for path in unrestored)
                + "; the original text is kept in "
                + ", ".join(str(backup) for backup in sorted(keep))
            ) from error
        raise
    finally:
        for staging in staged.values():
            staging.unlink(missing_ok=True)
        for backup in backups.values():
            if backup not in keep:
                backup.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    source_name, source_bytes = load_source_bytes(args.url, args.file)
    workbook_name, workbook_bytes = extract_economy_workbook_bytes(
        source_name, source_bytes
    )
    series_values = extract_annual_series_from_xlsx(workbook_bytes)

    # The economy tables' contents sheet names their release; the file name
    # or URL is the fallback, and --release-month/--release-year must agree.
    economy_release = infer_workbook_release(workbook_bytes)
    if args.release_month and args.release_year:
        if args.release_month.lower() not in MONTHS:
            raise ValueError(
                f"--release-month must be a month name, not {args.release_month!r}"
            )
        month = args.release_month.capitalize()
        year = args.release_year
        if economy_release not in (None, (month, year)):
            raise ValueError(
                f"The economy tables are from {economy_release[0]} "
                f"{economy_release[1]}, not {month} {year} as "
                "--release-month and --release-year say"
            )
    elif args.release_month or args.release_year:
        raise ValueError("Pass both --release-month and --release-year together")
    else:
        month, year = economy_release or infer_release(f"{source_name} {workbook_name}")

    forecast_start_year = args.forecast_start_year or infer_forecast_start_year(
        month, year
    )
    source_yaml_path = args.yaml_path or get_yoy_growth_path()
    write_gaps = not args.skip_statutory_gaps and args.output is None
    if args.gaps_only and not write_gaps:
        raise ValueError("--gaps-only cannot be combined with --output")
    if write_gaps and not (args.receipts_url or args.receipts_file):
        message = (
            "Pass --receipts-file or --receipts-url so September CPI uses the "
            "OBR's September forecast, or --skip-statutory-gaps"
        )
        if not args.dry_run:
            raise ValueError(message)
        print(f"Warning: {message}")
    has_previous_receipts = bool(
        args.previous_receipts_url or args.previous_receipts_file
    )
    if args.gaps_only and has_previous_receipts:
        raise ValueError(
            "--gaps-only leaves yoy_growth.yaml alone, so it cannot update the "
            "receipts growth series from --previous-receipts-file or "
            "--previous-receipts-url"
        )
    write_receipts = not args.gaps_only and not args.skip_receipts_growth
    if write_receipts and not (
        has_previous_receipts and (args.receipts_url or args.receipts_file)
    ):
        message = (
            "Pass the receipts tables (--receipts-file or --receipts-url) and the "
            "previous EFO's (--previous-receipts-file or --previous-receipts-url) "
            "so the receipts growth series move to this EFO, or "
            "--skip-receipts-growth"
        )
        if not args.dry_run:
            raise ValueError(message)
        print(f"Warning: {message}")
        write_receipts = False

    print_summary(series_values, forecast_start_year, args.forecast_years)
    receipts_bytes = None
    if args.receipts_url or args.receipts_file:
        receipts_name, receipts_bytes = load_source_bytes(
            args.receipts_url, args.receipts_file
        )
        receipts_release = resolve_release(receipts_bytes, receipts_name)
        # Both the receipts growth series and the September CPI gap read
        # these tables, so they must be identifiably this EFO's.
        if receipts_release is None:
            raise ValueError(
                "Could not tell which EFO the receipts tables are from; name the "
                "file with its release, e.g. receipts_march_2026.xlsx"
            )
        if receipts_release != (month, year):
            raise ValueError(
                "The receipts tables are from "
                f"{receipts_release[0]} {receipts_release[1]} but the economy "
                f"tables are from {month} {year}"
            )
    receipts_growth = None
    if write_receipts:
        previous_name, previous_bytes = load_source_bytes(
            args.previous_receipts_url, args.previous_receipts_file
        )
        previous_release = resolve_release(previous_bytes, previous_name)
        if previous_release is None:
            raise ValueError(
                "Could not tell which EFO the previous receipts tables are from; "
                "name the file with its release, e.g. receipts_march_2025.xlsx"
            )
        if release_order(previous_release) >= release_order((month, year)):
            raise ValueError(
                "The previous receipts tables "
                f"({previous_release[0]} {previous_release[1]}) must come from "
                f"an EFO before {month} {year}"
            )
        receipts_growth = compute_receipts_growth(receipts_bytes, previous_bytes)
        print_receipts_summary(
            receipts_growth, population_growth(source_yaml_path.read_text())
        )
    # The OBR publishes the national living wage's levels in the economy
    # tables, so the importer refreshes it with the economy series unless
    # --skip-national-living-wage leaves it alone.
    level_growth = None
    if not args.gaps_only and not args.skip_national_living_wage:
        level_growth = compute_level_growth(workbook_bytes)
    calendar_values = (
        read_calendar_values(source_yaml_path) if args.gaps_only else series_values
    )
    # Gaps are only built when they are written, so a growth-only run
    # (--output or --skip-statutory-gaps) never needs September CPI.
    statutory_gaps = (
        compute_statutory_forecast_gaps(
            workbook_bytes,
            forecast_start_year,
            args.forecast_years,
            receipts_bytes,
            calendar_values,
        )
        if write_gaps
        else {}
    )
    for key, gaps in statutory_gaps.items():
        window = ", ".join(
            f"{y}: {format_gap(g.value)}" for y, g in sorted(gaps.items())
        )
        print(f"- forecast gap {key}: {window}")

    # Render and check every file before writing any, so a failure cannot
    # leave growth and gaps from different forecasts.
    outputs: dict[Path, str] = {}
    if not args.gaps_only:
        outputs[args.output or source_yaml_path] = render_yoy_growth_yaml(
            source_yaml_path.read_text(),
            series_values,
            month,
            year,
            forecast_start_year,
            args.forecast_years,
        )
    if receipts_growth is not None:
        yoy_path = args.output or source_yaml_path
        outputs[yoy_path] = render_receipts_growth_yaml(
            outputs[yoy_path], receipts_growth, (month, year), previous_release
        )
    if level_growth is not None:
        yoy_path = args.output or source_yaml_path
        # The importer chooses the growth that keeps each penny from the years
        # the rendered file keeps before the table, so it prints the summary
        # after rendering the other series.
        print_level_summary(
            penny_preserving_level_growth(outputs[yoy_path], level_growth)
        )
        outputs[yoy_path] = render_level_series_yaml(
            outputs[yoy_path], level_growth, (month, year)
        )
    if write_gaps:
        gap_dir = get_forecast_gap_dir(source_yaml_path)
        for spec in STATUTORY_GAP_SPECS:
            gap_path = gap_dir / f"{spec.key}.yaml"
            outputs[gap_path] = render_forecast_gap_yaml(
                gap_path.read_text(), spec, statutory_gaps[spec.key], month, year
            )

    if args.dry_run:
        return 0
    write_all_or_none(outputs)
    for path in outputs:
        print(f"Updated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
