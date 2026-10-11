from __future__ import annotations

import argparse
import copy
import os
import re
import shutil
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
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
FOOTNOTE_RE = re.compile(r"(?<=[a-z])\d+$")
VALUE_LINE_RE = re.compile(r"^\s*(\d{4})-\d{2}-\d{2}:")


@dataclass(frozen=True)
class ReceiptsSeriesSpec:
    """A line of the OBR receipts tables, grown by a yoy_growth.yaml series.

    ``path`` is the series' place under ``obr``. The table is found by its
    title, not its number, because numbers move between EFOs: current
    receipts on a cash basis are Table 3.8 in March 2026 and 3.9 in March
    2025. Titles and row labels are compared lowercased, without footnote
    markers.
    """

    path: tuple[str, ...]
    title: str
    row: str


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
)


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
    year is the ratio of this EFO's consecutive levels.
    """

    values: dict[int, float]
    line: ReceiptsLine
    previous_line: ReceiptsLine


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


def table_title(rows: list[dict[str, str | None]]) -> tuple[str, str] | None:
    """The number and normalised title of a table, e.g. ("3.8", "current
    receipts (on a cash basis)"), from the first title cell in its top rows."""
    for row in rows[:3]:
        for column in sorted(row, key=column_index):
            match = TABLE_TITLE_RE.match(" ".join(str(row[column] or "").split()))
            if match:
                return match.group(1), receipts_label(match.group(2))
    return None


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


def find_receipts_line(
    sheets: dict[str, list[dict[str, str | None]]], spec: ReceiptsSeriesSpec
) -> ReceiptsLine:
    """The one row labelled ``spec.row`` in the table titled ``spec.title``."""
    matches = []
    for sheet, rows in sheets.items():
        title = table_title(rows)
        if title is None or title[1] != spec.title:
            continue
        years: dict[str, int] = {}
        markers: dict[str, int] = {}
        for row in rows:
            row_years = _fiscal_year_columns(row)
            if row_years:
                years = row_years
                continue
            row_markers = {
                normalise_label(value): column_index(column)
                for column, value in row.items()
                if normalise_label(value) in ("outturn", "forecast")
            }
            if row_markers:
                markers = row_markers
                continue
            if not years:
                continue
            first_year_column = min(column_index(column) for column in years)
            labels = [
                value
                for column, value in sorted(
                    row.items(), key=lambda item: column_index(item[0])
                )
                if column_index(column) < first_year_column and normalise_label(value)
            ]
            if labels and receipts_label(labels[0]) == spec.row:
                matches.append((title[0], sheet, labels[0], row, years, markers))

    name = ".".join(spec.path)
    if len(matches) != 1:
        found = ", ".join(f"sheet {match[1]}" for match in matches) or "none"
        raise ValueError(
            f'Expected one "{spec.row}" row in the "{spec.title}" table for '
            f"{name}; found {found}"
        )
    table, sheet, label, row, years, markers = matches[0]
    where = f"Table {table} (sheet {sheet})"
    levels = {}
    for column, year in years.items():
        if row.get(column) in (None, ""):
            raise ValueError(f"{where} has no {fiscal_year_label(year)} {name} value")
        levels[year] = float(row[column])
    ordered = sorted(levels)
    if ordered != list(range(ordered[0], ordered[-1] + 1)):
        raise ValueError(f"{where} skips a year: {ordered}")
    return ReceiptsLine(
        table=table,
        label=" ".join(str(label).split()).rstrip("0123456789"),
        levels=levels,
        outturn_years=_outturn_years(years, markers, where),
    )


def compute_receipts_growth(
    xlsx_bytes: bytes, previous_xlsx_bytes: bytes
) -> dict[tuple[str, ...], ReceiptsGrowth]:
    """Growth in each receipts line, from an EFO's receipts tables and an
    earlier EFO's, whose outturn is the base for the first year's growth.

    The first year must be outturn in this EFO, and the year before it
    outturn in the earlier one (March 2025 for March 2026).
    """
    sheets = read_workbook_sheets(xlsx_bytes)
    previous_sheets = read_workbook_sheets(previous_xlsx_bytes)
    result = {}
    for spec in RECEIPTS_SERIES_SPECS:
        name = ".".join(spec.path)
        line = find_receipts_line(sheets, spec)
        previous = find_receipts_line(previous_sheets, spec)
        first_year = min(line.levels)
        base_year = first_year - 1
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
        values = {}
        for year in sorted(line.levels):
            if levels[year - 1] <= 0:
                raise ValueError(
                    f"{name}: cannot grow from {fiscal_year_label(year - 1)} "
                    f"receipts of {levels[year - 1]}"
                )
            values[year] = round(levels[year] / levels[year - 1] - 1, 6) + 0.0
        result[spec.path] = ReceiptsGrowth(values, line, previous)
    return result


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
    lines[start:end], from its key through its last non-blank child line."""
    pattern = re.compile(rf"^ {{{indent}}}{re.escape(key)}:(\s|$)")
    for first in range(start, end):
        if not pattern.match(lines[first]):
            continue
        last = first + 1
        for index in range(first + 1, end):
            if not lines[index].strip():
                continue
            if _indent(lines[index]) <= indent:
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
    table = f"Table {published.table}"
    if previous.table != published.table:
        table += f" ({previous_month} {previous_year}: Table {previous.table})"
    pad = " " * indent
    lines = kept + [
        f"{pad}# Outturn ({fiscal_year_label(first_year)} over "
        f"{fiscal_year_label(first_year - 1)}) from OBR EFO {month} {year} over "
        f'{previous_month} {previous_year}, receipts {table} "{published.label}"',
        f"{pad}{first_year}-01-01: {format_growth(growth.values[first_year])}",
    ]
    later = sorted(y for y in growth.values if y > first_year)
    for kind in ("Outturn", "Forecast"):
        years = [
            y for y in later if (y in published.outturn_years) == (kind == "Outturn")
        ]
        if not years:
            continue
        span = f"{years[0]}" if len(years) == 1 else f"{years[0]}-{years[-1]}"
        lines.append(
            f"{pad}# {kind} ({span}) from OBR EFO {month} {year}, receipts "
            f"Table {published.table}"
        )
        lines += [f"{pad}{y}-01-01: {format_growth(growth.values[y])}" for y in years]
    lines.append(
        f"{pad}# Beyond the OBR forecast: the average_earnings long-run path above"
    )
    lines += [f"{pad}{y}-01-01: {format_growth(v)}" for y, v in sorted(tail.items())]
    return lines


def receipts_references(
    growth: ReceiptsGrowth,
    release: tuple[str, int],
    previous_release: tuple[str, int],
) -> list[dict[str, str]]:
    month, year = release
    previous_month, previous_year = previous_release
    base_year = min(growth.values) - 1
    return [
        {
            "title": f"OBR EFO {month} {year} (detailed forecast tables, receipts, "
            f"Table {growth.line.table})",
            "href": build_efo_href(month, year),
        },
        {
            "title": f"OBR EFO {previous_month} {previous_year} (detailed forecast "
            f"tables, receipts, Table {growth.previous_line.table}; "
            f"{fiscal_year_label(base_year)} outturn)",
            "href": build_efo_href(previous_month, previous_year),
        },
    ]


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
    average_earnings as ``content`` holds it. The result is checked to
    differ from ``content`` only in those values and references.
    """
    before = yaml.safe_load(content)
    expected = copy.deepcopy(before)
    lines = content.split("\n")
    for path, series in growth.items():
        tail = average_earnings_path(content, max(series.values))
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
            old_values, entry_indent, series, tail, release, previous_release
        )
        lines[values_start + 1 : values_end] = new_values

        start, end = _series_block(lines, ("obr", *path))
        metadata = _yaml_block(lines, "metadata", indent, start, end)
        ref_start, ref_end = _yaml_block(
            lines, "reference", indent + 2, metadata[0], metadata[1]
        )
        pad = " " * (indent + 2)
        lines[ref_start:ref_end] = [f"{pad}reference:"] + [
            text
            for reference in references
            for text in (
                f"{pad}  - title: {reference['title']}",
                f"{pad}    href: {reference['href']}",
            )
        ]

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
        node["metadata"]["reference"] = references

    rendered = "\n".join(lines)
    if yaml.safe_load(rendered) != expected:
        raise ValueError(
            "Rewriting the receipts growth series changed more than their "
            "values and references"
        )
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
    match = MONTH_RE.search(source_name)
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
            section = replace_year_value(
                section, target_year, series_values[spec.key][target_year]
            )

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


def print_receipts_summary(growth: dict[tuple[str, ...], ReceiptsGrowth]) -> None:
    print(f"Updating {len(growth)} OBR receipts growth series")
    for path, series in growth.items():
        window = ", ".join(
            f"{year}: {format_growth(value)}"
            for year, value in sorted(series.values.items())
        )
        print(f"- {'.'.join(path)} (Table {series.line.table}): {window}")


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
            "business_rates) that project corporate SDLT and business rates"
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

    if args.release_month and args.release_year:
        month = args.release_month.capitalize()
        year = args.release_year
    elif args.release_month or args.release_year:
        raise ValueError("Pass both --release-month and --release-year together")
    else:
        month, year = infer_release(f"{source_name} {workbook_name}")

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
        if receipts_release not in (None, (month, year)):
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
        print_receipts_summary(receipts_growth)
    calendar_values = (
        read_calendar_values(source_yaml_path) if args.gaps_only else series_values
    )
    statutory_gaps = compute_statutory_forecast_gaps(
        workbook_bytes,
        forecast_start_year,
        args.forecast_years,
        receipts_bytes,
        calendar_values,
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
