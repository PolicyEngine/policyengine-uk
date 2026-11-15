"""Build ``lha_published_rates.csv.gz`` from the published LHA tables.

Every source file is listed, with its URL and SHA-256, in
``lha_published_rates_sources.csv`` next to the output. The build downloads each
file (or reads it from a cache), checks its hash, parses it, and writes one row
per determination year, Broad Rental Market Area and LHA category:

- ``rate``: the weekly Housing Benefit LHA in force from April of ``year``;
- ``percentile_30``: the weekly rent at the 30th percentile of the list of
  rents for the twelve months to the previous September. The VOA publishes it
  for England every year, including frozen ones. Where a publisher does not, it
  is filled for the years rates were reset to the 30th percentile with the
  published rate, which reproduces the determination;
- ``uc_rate``: the monthly Universal Credit LHA in force from April of ``year``;
- ``uc_percentile_30``: the monthly percentile rent, filled in reset years from
  ``uc_rate`` wherever the Housing Benefit rate equals its percentile rent, so
  no maximum or anomalous-rate adjustment moved it.

Spreadsheet readers are not runtime dependencies, so run the build with them:

    uv run --with openpyxl --with xlrd --with odfpy --with beautifulsoup4 \
        python scripts/build_lha_published_rates.py --cache ~/.cache/lha

gov.scot and the NIHE site can refuse scripted downloads; the NIHE pages are
read from the Internet Archive's original-bytes (``id_``) captures. A file that
will not download can be placed in the cache by hand under its ``file`` name,
and the build still checks its hash.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
import xml.etree.ElementTree as ElementTree
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from policyengine_uk.utils.lha import (
    CATEGORIES,
    LHA_DIRECTORY,
    PUBLISHED_RATES_PATH,
    RESET_YEARS,
    round_half_up,
)
from policyengine_uk.variables.household.demographic.locations import BRMAName

SOURCES_PATH = LHA_DIRECTORY / "lha_published_rates_sources.csv"

USER_AGENT = "Mozilla/5.0 (compatible; policyengine-uk LHA build)"

# Published BRMA spellings that differ from the enum labels.
ALIASES = {
    "flint": "FLINTSHIRE",
    "renfrewshire inverclyde": "RENFREWSHIRE_AND_INVERCLYDE",
    "weston super mare": "WESTON_S_MARE",
}


def normalise(name: str) -> str:
    name = name.lower().replace("&", " and ").replace("-", " ").replace("'", "")
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


_ENUM_BY_NAME = {}
for member in BRMAName:
    _ENUM_BY_NAME.setdefault(normalise(member.value), member.name)
    _ENUM_BY_NAME.setdefault(normalise(member.name.replace("_", " ")), member.name)


def brma_enum(published: str) -> str:
    key = normalise(published)
    if key in ALIASES:
        return ALIASES[key]
    if key not in _ENUM_BY_NAME:
        raise KeyError(f"Unrecognised BRMA name {published!r}")
    return _ENUM_BY_NAME[key]


def money(value) -> float | None:
    if isinstance(value, str):
        value = value.replace("£", "").replace(",", "").strip()
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(number) else number


def fetch(source: pd.Series, cache: Path) -> Path:
    path = cache / source.file
    if not path.exists():
        request = Request(source.url, headers={"User-Agent": USER_AGENT})
        with urlopen(request) as response:
            path.write_bytes(response.read())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != source.sha256:
        raise ValueError(f"{source.id}: {path.name} has SHA-256 {digest}")
    return path


def brma_block(frame: pd.DataFrame) -> list[tuple[str, list[float]]]:
    """Rows of (BRMA, five category values) from a BRMA-by-category table.

    The BRMA is the first text cell of a row, followed by the five weekly or
    monthly category columns; monthly-equivalent columns further right are
    ignored. Header, title and note rows have no five numbers and are skipped.
    """
    rows = []
    for cells in frame.itertuples(index=False):
        cells = list(cells)
        first = next(
            (i for i, c in enumerate(cells) if isinstance(c, str) and c.strip()),
            None,
        )
        if first is None:
            continue
        values = [money(c) for c in cells[first + 1 : first + 7]]
        # Some Welsh tables put a five-digit BRMA code before the rates.
        code = values[0]
        if code is not None and code == int(code) and 10_000 <= code < 100_000:
            values = values[1:]
        values = values[:5]
        if len(values) == 5 and all(v is not None for v in values):
            rows.append((cells[first].strip(), values))
    return rows


def parse_voa(path: Path, source: pd.Series) -> list[dict]:
    """VOA Housing Benefit tables: the year's rates and percentile rents."""
    out = []
    for part in source.location.split(";"):
        measure, sheet = part.split("=")
        frame = pd.read_excel(path, sheet_name=sheet, header=None)
        title = " ".join(str(c) for c in frame.iloc[:2].to_numpy().ravel())
        expected = (
            "30th Percentile" if measure == "percentile_30" else f"April {source.year}"
        )
        if expected.lower() not in title.lower():
            raise ValueError(f"{source.id} {sheet}: header {title!r}")
        for name, values in brma_block(frame):
            out += [
                dict(
                    year=int(source.year),
                    brma=brma_enum(name),
                    lha_category=c,
                    measure=measure,
                    value=v,
                )
                for c, v in zip(CATEGORIES, values)
            ]
    return out


def parse_dwp_uc(path: Path, source: pd.Series) -> list[dict]:
    """DWP monthly Universal Credit rates, one table or one sheet per year."""
    if path.suffix == ".csv":
        tables = {
            int(source.year): pd.read_csv(
                path, header=None, dtype=str, encoding="latin-1"
            )
        }
    else:
        book = pd.ExcelFile(path, engine="odf")
        sheets = [s for s in book.sheet_names if not s.lower().startswith("expl")]
        if str(source.year).isdigit():
            if len(sheets) != 1:
                raise ValueError(f"{source.id}: sheets {book.sheet_names}")
            tables = {int(source.year): pd.read_excel(book, sheets[0], header=None)}
        else:
            tables = {
                int(re.search(r"\d{4}", s).group()): pd.read_excel(book, s, header=None)
                for s in sheets
            }
    out = []
    for year, frame in tables.items():
        for name, values in brma_block(frame):
            out += [
                dict(
                    year=year,
                    brma=brma_enum(name),
                    lha_category=c,
                    measure="uc_rate",
                    value=v,
                )
                for c, v in zip(CATEGORIES, values)
            ]
    return out


ODS_TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
ODS_OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"


def read_ods(path: Path) -> dict[str, list[list[str]]]:
    """Sheets of an ODS file as lists of rows of cell strings.

    A small reader for the Welsh tables, whose long runs of repeated empty
    cells stall pandas' odf engine. Numeric cells give their stored value.
    """
    root = ElementTree.fromstring(zipfile.ZipFile(path).read("content.xml"))
    sheets = {}
    for table in root.iter(ODS_TABLE + "table"):
        rows = []
        for row in table.iter(ODS_TABLE + "table-row"):
            cells = []
            for cell in row:
                if cell.tag not in (
                    ODS_TABLE + "table-cell",
                    ODS_TABLE + "covered-table-cell",
                ):
                    continue
                repeat = min(
                    int(cell.get(ODS_TABLE + "number-columns-repeated", "1")), 64
                )
                value = cell.get(ODS_OFFICE + "value")
                text = value if value is not None else "".join(cell.itertext()).strip()
                cells += [text] * repeat
            while cells and not cells[-1]:
                cells.pop()
            if cells:
                rows.append(cells)
        sheets[table.get(ODS_TABLE + "name")] = rows
    return sheets


WELSH_CATEGORIES = {
    "shared accommodation": "A",
    "1 bedroom": "B",
    "2 bedroom": "C",
    "3 bedroom": "D",
    "4 bedroom": "E",
}


def parse_rent_officers_wales(path: Path, source: pd.Series) -> list[dict]:
    """Rent Officers Wales weekly tables.

    Each BRMA has a header row (its code and name) followed by one row per
    category. The rate column is headed "New LHA rates for Apr <year>" and the
    percentile column "New 30th percentile from list of rents". Cross-border
    BRMAs that the VOA determines (West Cheshire) are left to the VOA tables.
    """
    sheets = read_ods(path)
    rows = next(rows for name, rows in sheets.items() if "weekly" in name.lower())
    title = " ".join(" ".join(r) for r in rows[:2])
    if f"april {source.year}" not in title.lower():
        raise ValueError(f"{source.id}: title {title!r}")
    labels: dict[int, str] = {}
    body_start = None
    for index, row in enumerate(rows):
        if any(normalise(c) in WELSH_CATEGORIES for c in row):
            body_start = index - 1
            break
        for column, cell in enumerate(row):
            labels[column] = f"{labels.get(column, '')} {cell}".strip()
    columns = {}
    for column, label in labels.items():
        text = label.lower()
        if "new lha rates" in text:
            columns["rate"] = column
        elif "30th percentile" in text:
            columns["percentile_30"] = column
    if "rate" not in columns:
        raise ValueError(f"{source.id}: no rate column in {labels}")
    out, brma = [], None
    for row in rows[body_start:]:
        text = [c for c in row if c]
        if not text:
            continue
        label = normalise(text[0])
        if label in WELSH_CATEGORIES:
            if brma is None:
                continue
            for measure, column in columns.items():
                value = money(row[column]) if column < len(row) else None
                if value is not None:
                    out.append(
                        dict(
                            year=int(source.year),
                            brma=brma,
                            lha_category=WELSH_CATEGORIES[label],
                            measure=measure,
                            value=value,
                        )
                    )
            continue
        # The BRMA's code and name, sometimes in one cell; the April 2022 table
        # has a stray figure in the South Gwynedd header row.
        name = " ".join(c for c in text if money(c) is None)
        name = re.sub(r"^\d+\s+", "", name).strip()
        brma = None if normalise(name) == "west cheshire" else brma_enum(name)
    return out


class _HtmlTables(HTMLParser):
    """Visible text of every table cell in an HTML page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self._table, self._row, self._cell = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def html_tables(path: Path) -> list[list[list[str]]]:
    parser = _HtmlTables()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser.tables


SCOTTISH_CATEGORIES = {
    "1 bedroom shared": "A",
    "1 bedroom": "B",
    "2 bedroom": "C",
    "3 bedroom": "D",
    "4 bedroom": "E",
}


def scottish_brma(name: str) -> str:
    # Spelling variants on gov.scot: council lists in brackets, "Highlands",
    # "Renfrewshire/ Inverclyde", stray emphasis markers and a curly quote.
    name = name.split("(", 1)[0].replace("**", "").replace("”", " ")
    name = name.replace("/", " and ").replace("Highlands", "Highland")
    return brma_enum(name)


def parse_gov_scot(path: Path, source: pd.Series) -> list[dict]:
    """Scottish Government (Rent Service Scotland) annual LHA pages.

    The first table is the headline weekly rates by BRMA (categories A to E
    across). The second is the methodology table: a row per BRMA, then a row
    per category giving the earlier rate (some years), the 30th percentile of
    the list of rents, and the rate determined.
    """
    tables = html_tables(path)
    out = []
    for part in source.location.split(";"):
        measure, index = part.split("=")
        table = tables[int(index)]
        if measure == "rate":
            for row in table:
                values = [money(c) for c in row[1:6]] if len(row) >= 6 else []
                if row and row[0] and len(values) == 5 and None not in values:
                    out += [
                        dict(
                            year=int(source.year),
                            brma=scottish_brma(row[0]),
                            lha_category=c,
                            measure="rate",
                            value=v,
                        )
                        for c, v in zip(CATEGORIES, values)
                    ]
        else:
            brma = None
            for row in table:
                if not row or not row[0]:
                    continue
                label = row[0].strip().lower()
                if label in SCOTTISH_CATEGORIES:
                    values = [money(c) for c in row[1:] if c]
                    out.append(
                        dict(
                            year=int(source.year),
                            brma=brma,
                            lha_category=SCOTTISH_CATEGORIES[label],
                            measure="percentile_30",
                            value=values[1],
                        )
                    )
                elif label != "brma":
                    brma = scottish_brma(row[0])
    return out


NIHE_BRMAS = {
    "Belfast": "BELFAST",
    "Lough Neagh Lower": "LOUGH_NEAGH_LOWER",
    "Lough Neagh Upper": "LOUGH_NEAGH_UPPER",
    "North": "NORTH_NI",
    "North West": "NORTH_WEST_NI",
    "South East": "SOUTH_EAST_NI",
    "South": "SOUTH_NI",
    "South West": "SOUTH_WEST_NI",
}
NI_MONEY = re.compile(r"£\s*([0-9]+(?:,[0-9]{3})*\.[0-9]{2})(?![0-9])")


def _text(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def _nihe_brma(name: str) -> str:
    name = re.sub(r"^BRMA\s+[0-9]+\s+", "", name)
    name = re.sub(r"\s+BRMA(?:\s+\(.*\))?$", "", name)
    return NIHE_BRMAS[name]


def _nihe_category(label: str) -> str:
    label = " ".join(label.split()).lower()
    if label.startswith(("single room", "shared room", "shared accommodation")):
        return "A"
    match = re.match(r"([1-4])\s*-?\s*bed", label)
    if match:
        return "BCDE"[int(match[1]) - 1]
    raise ValueError(f"Unrecognised category {label!r}")


def _amount(text: str) -> float:
    figures = NI_MONEY.findall(text)
    if len(figures) != 1:
        raise ValueError(f"Expected one pound figure in {text!r}")
    return float(figures[0].replace(",", ""))


def parse_nihe(path: Path, source: pd.Series) -> list[dict]:
    """Northern Ireland Housing Executive pages and nidirect's UC table.

    NIHE has published its weekly rates in three layouts: a table with a
    column per BRMA (2015 to 2018), and collapsible panels per BRMA (2019 on).
    Its calculation pages give the 30th percentile in a table per BRMA (2015
    to 2017) or in panels (2018). nidirect publishes Northern Ireland's
    monthly Universal Credit rates as a BRMA by category table.
    """
    from bs4 import BeautifulSoup

    data = path.read_bytes()
    try:
        html = data.decode("utf-8")
    except UnicodeDecodeError:
        # Old NIHE pages declare UTF-8 but contain CP1252 bytes.
        html = data.decode("cp1252")
    soup = BeautifulSoup(html, "html.parser")
    year, mode = int(source.year), source.location
    cells = []
    if mode == "hb_transposed":
        (table,) = [
            t
            for t in soup.find_all("table")
            if "Broad Rental Market Area" in t.get_text()
        ]
        rows = table.find_all("tr")
        names = [_text(c) for c in rows[0].find_all(["th", "td"], recursive=False)][1:]
        for row in rows[1:]:
            row_cells = row.find_all(["th", "td"], recursive=False)
            if row_cells and "rate per week" in _text(row_cells[0]).lower():
                category = _nihe_category(_text(row_cells[0]))
                for name, cell in zip(names, row_cells[1:]):
                    cells.append((name, category, "rate", _amount(_text(cell))))
    elif mode == "hb_accordion":
        for panel in soup.select(".collapsible_panel"):
            heading = panel.select_one("h3.collapsible_panel-title")
            if heading is None:
                continue
            for item in panel.select(".collapsible_panel-content li"):
                text = _text(item)
                cells.append(
                    (_text(heading), _nihe_category(text), "rate", _amount(text))
                )
    elif mode == "percentile_tables":
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            headers = [
                _text(c) for c in rows[0].find_all(["th", "td"], recursive=False)
            ]
            columns = [
                i
                for i, h in enumerate(headers)
                if f"30th percentile rate for {year}" in h
            ]
            if not columns:
                continue
            heading = next(
                h
                for h in table.find_all_previous(["h2", "h3", "h4"])
                if h.find("table") is None and re.match(r"BRMA\s+[0-9]+\s+", _text(h))
            )
            for row in rows[1:]:
                row_cells = row.find_all(["th", "td"], recursive=False)
                cells.append(
                    (
                        _text(heading),
                        _nihe_category(_text(row_cells[0])),
                        "percentile_30",
                        _amount(_text(row_cells[columns[0]])),
                    )
                )
    elif mode == "percentile_accordion":
        for panel in soup.select(".collapsible_panel"):
            name = _text(panel.select_one("h3.collapsible_panel-title"))
            for paragraph in panel.select_one(".collapsible_panel-content").find_all(
                "p"
            ):
                text = _text(paragraph)
                if f"30th percentile rate for {year}:" in text:
                    label = _text(paragraph.find_previous("h3"))
                    cells.append(
                        (name, _nihe_category(label), "percentile_30", _amount(text))
                    )
    elif mode == "uc_table":
        (table,) = [
            t
            for t in soup.find_all("table")
            if "Shared Room Rate" in t.get_text() and "Belfast BRMA" in t.get_text()
        ]
        for row in table.find_all("tr")[1:]:
            row_cells = row.find_all(["th", "td"], recursive=False)
            for category, cell in zip(CATEGORIES, row_cells[1:]):
                cells.append(
                    (_text(row_cells[0]), category, "uc_rate", _amount(_text(cell)))
                )
    else:
        raise ValueError(f"{source.id}: unknown NIHE layout {mode}")
    if len(cells) != 40:
        raise ValueError(f"{source.id}: {len(cells)} cells, expected 40")
    return [
        dict(
            year=year,
            brma=_nihe_brma(name),
            lha_category=category,
            measure=measure,
            value=value,
        )
        for name, category, measure, value in cells
    ]


PARSERS = {
    "voa": parse_voa,
    "dwp_uc": parse_dwp_uc,
    "rent_officers_wales": parse_rent_officers_wales,
    "gov_scot": parse_gov_scot,
    "nihe": parse_nihe,
}


def build(cache: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    cache.mkdir(parents=True, exist_ok=True)
    sources = pd.read_csv(SOURCES_PATH, dtype=str)
    records = []
    for source in sources.itertuples(index=False):
        rows = PARSERS[source.parser](fetch(source, cache), source)
        records += [dict(row, source=source.id) for row in rows]
    long = pd.DataFrame(records)
    # A few early tables print unrounded figures; rates are whole pence
    # (Sch 3B para 2(10)).
    long["value"] = round_half_up(long.value)

    duplicated = long.duplicated(
        ["year", "brma", "lha_category", "measure"], keep=False
    )
    if duplicated.any():
        raise ValueError(f"Duplicate cells:\n{long[duplicated].head(20)}")

    table = long.pivot_table(
        index=["year", "brma", "lha_category"], columns="measure", values="value"
    ).reset_index()
    for measure in ("rate", "percentile_30", "uc_rate"):
        if measure not in table:
            table[measure] = np.nan

    reset = table.year.isin(RESET_YEARS)
    table["percentile_30"] = table.percentile_30.where(
        table.percentile_30.notna() | ~reset, table.rate
    )
    unadjusted = (table.rate - table.percentile_30).abs() < 0.005
    table["uc_percentile_30"] = table.uc_rate.where(reset & unadjusted)
    table = table[
        [
            "year",
            "brma",
            "lha_category",
            "rate",
            "percentile_30",
            "uc_rate",
            "uc_percentile_30",
        ]
    ].sort_values(["year", "brma", "lha_category"])
    return table, long


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "lha")
    parser.add_argument("--output", type=Path, default=PUBLISHED_RATES_PATH)
    args = parser.parse_args(argv)
    table, _ = build(args.cache)
    table.to_csv(args.output, index=False, float_format="%.2f")
    print(f"Wrote {len(table)} rows to {args.output}")
    return 0
