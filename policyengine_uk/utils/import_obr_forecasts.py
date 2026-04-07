from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
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
MONTH_RE = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december)[-_ ]+(\d{4})",
    re.IGNORECASE,
)


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
    content = yaml_path.read_text()
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

    yaml_path.write_text(content)


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
        "--dry-run",
        action="store_true",
        help="Print the extracted values without updating yoy_growth.yaml",
    )
    return parser


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
    print_summary(series_values, forecast_start_year, args.forecast_years)

    if args.dry_run:
        return 0

    source_yaml_path = args.yaml_path or get_yoy_growth_path()
    target_yaml_path = args.output or source_yaml_path
    if target_yaml_path != source_yaml_path:
        target_yaml_path.write_text(source_yaml_path.read_text())
    update_yoy_growth_yaml(
        yaml_path=target_yaml_path,
        series_values=series_values,
        month=month,
        year=year,
        forecast_start_year=forecast_start_year,
        forecast_years=args.forecast_years,
    )
    print(f"Updated {target_yaml_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
