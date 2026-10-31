import os
from dataclasses import replace
from datetime import date
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pytest
import yaml
from hypothesis import event, given, settings
from hypothesis import strategies as st

from policyengine_uk.utils import import_obr_forecasts

from policyengine_uk.utils.import_obr_forecasts import (
    RECEIPTS_SERIES_SPECS,
    SERIES_SPECS,
    STATUTORY_GAP_SPECS,
    _sheet_paths,
    ForecastGap,
    MACHINE_GAMES_HIGHER_STAKE_SHARE,
    ReceiptsSeriesSpec,
    machine_games_spec,
    average_earnings_path,
    compute_receipts_growth,
    find_receipts_line,
    format_gap,
    format_growth,
    get_yoy_growth_path,
    infer_workbook_release,
    main,
    read_calendar_values,
    read_workbook_sheets,
    render_forecast_gap_yaml,
    render_receipts_growth_yaml,
    render_yoy_growth_yaml,
    build_efo_href,
    compute_statutory_forecast_gaps,
    extract_annual_series_from_xlsx,
    extract_september_cpi_from_receipts,
    infer_forecast_start_year,
    infer_release,
    update_forecast_gap_yaml,
    update_yoy_growth_yaml,
)


def make_inline_cell(ref: str, value: str) -> str:
    return f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'


def make_number_cell(ref: str, value: float) -> str:
    return f'<c r="{ref}"><v>{value}</v></c>'


def make_sheet(rows: dict[int, list[str]]) -> bytes:
    row_xml = []
    for row_num in sorted(rows):
        row_xml.append(f'<row r="{row_num}">{"".join(rows[row_num])}</row>')
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(row_xml)}</sheetData>"
        "</worksheet>"
    )
    return xml.encode()


def make_test_xlsx(earnings_quarter: bool = True) -> bytes:
    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="1.6" sheetId="1" r:id="rId1"/>
    <sheet name="1.7" sheetId="2" r:id="rId2"/>
    <sheet name="1.16" sheetId="3" r:id="rId3"/>
  </sheets>
</workbook>
"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
</Relationships>
"""

    sheet_16 = make_sheet(
        {
            3: [make_inline_cell("Q3", "Average weekly earnings growth (per cent)")],
            97: [
                make_inline_cell("B97", "2025"),
                make_number_cell("Q97", 5.17),
            ],
            98: [
                make_inline_cell("B98", "2026"),
                make_number_cell("Q98", 3.33),
            ],
            **(
                {
                    99: [
                        make_inline_cell("B99", "2026Q2"),
                        make_number_cell("Q99", 3.67),
                    ]
                }
                if earnings_quarter
                else {}
            ),
        }
    )
    sheet_17 = make_sheet(
        {
            3: [
                make_inline_cell("C3", "RPI"),
                make_inline_cell("E3", "CPI"),
                make_inline_cell("F3", "CPIH"),
                make_inline_cell(
                    "H3",
                    "Mortgage interest payments on dwellings (per cent change on a year earlier)",
                ),
                make_inline_cell(
                    "I3",
                    "Actual rents for housing (per cent change on a year earlier)",
                ),
            ],
            98: [
                make_inline_cell("B98", "2025"),
                make_number_cell("C98", 4.33),
                make_number_cell("E98", 3.45),
                make_number_cell("F98", 3.88),
                make_number_cell("H98", 9.52),
                make_number_cell("I98", 5.42),
            ],
            99: [
                make_inline_cell("B99", "2026"),
                make_number_cell("C99", 3.71),
                make_number_cell("E99", 2.48),
                make_number_cell("F99", 2.55),
                make_number_cell("H99", 7.97),
                make_number_cell("I99", 3.34),
            ],
            100: [
                make_inline_cell("B100", "2026Q3"),
                make_number_cell("C100", 3.2),
                make_number_cell("E100", 2.08),
                make_number_cell("F100", 2.3),
                make_number_cell("H100", 8.0),
                make_number_cell("I100", 3.3),
            ],
        }
    )
    sheet_116 = make_sheet(
        {
            3: [
                make_inline_cell(
                    "D3",
                    "House price index (per cent change on a year earlier)",
                )
            ],
            97: [
                make_inline_cell("B97", "2025"),
                make_number_cell("D97", 2.80),
            ],
            98: [
                make_inline_cell("B98", "2026"),
                make_number_cell("D98", 2.40),
            ],
        }
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_16)
        archive.writestr("xl/worksheets/sheet2.xml", sheet_17)
        archive.writestr("xl/worksheets/sheet3.xml", sheet_116)
    return buffer.getvalue()


def test_extract_annual_series_from_xlsx():
    series = extract_annual_series_from_xlsx(make_test_xlsx())

    assert series["average_earnings"] == {2025: 0.0517, 2026: 0.0333}
    assert series["rpi"] == {2025: 0.0433, 2026: 0.0371}
    assert series["consumer_price_index"] == {2025: 0.0345, 2026: 0.0248}
    assert series["cpih"] == {2025: 0.0388, 2026: 0.0255}
    assert series["mortgage_interest"] == {2025: 0.0952, 2026: 0.0797}
    assert series["rent"] == {2025: 0.0542, 2026: 0.0334}
    assert series["house_prices"] == {2025: 0.028, 2026: 0.024}


def test_release_inference_helpers():
    assert infer_release("Economy_Detailed_forecast_tables_November_2025.xlsx") == (
        "November",
        2025,
    )
    assert infer_forecast_start_year("March", 2026) == 2025
    assert build_efo_href("March", 2026) == (
        "https://obr.uk/efo/economic-and-fiscal-outlook-march-2026/"
    )


def test_update_yoy_growth_yaml_updates_forecast_window_only(tmp_path):
    yaml_path = tmp_path / "yoy_growth.yaml"
    yaml_path.write_text("""obr:
  rpi:
    values:
      2024-01-01: 0.0300
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2031-01-01: 0.0230
    metadata:
      reference:
        - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.7)
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
  average_earnings:
    values:
      2024-01-01: 0.0400
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2031-01-01: 0.0383
    metadata:
      reference:
        - title: Old
          href: https://example.com/old
  consumer_price_index:
    values:
      2024-01-01: 0.0200
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2031-01-01: 0.0200
    metadata:
      reference:
        - title: Old
          href: https://example.com/old
  cpih:
    values:
      2024-01-01: 0.0200
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2031-01-01: 0.0230
    metadata:
      reference:
        - title: Old
          href: https://example.com/old
  house_prices:
    values:
      2024-01-01: 0.0100
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2031-01-01: 0.0200
    metadata:
      reference:
        - title: Old
          href: https://example.com/old
  mortgage_interest:
    values:
      2024-01-01: 0.1000
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2031-01-01: 0.0300
    metadata:
      reference:
        - title: Old
          href: https://example.com/old
  rent:
    values:
      2024-01-01: 0.0500
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2031-01-01: 0.0200
    metadata:
      reference:
        - title: Old
          href: https://example.com/old
""")

    update_yoy_growth_yaml(
        yaml_path=yaml_path,
        series_values=extract_annual_series_from_xlsx(make_test_xlsx()),
        month="March",
        year=2026,
        forecast_start_year=2025,
        forecast_years=2,
    )

    content = yaml_path.read_text()
    assert "2024-01-01: 0.0300" in content
    assert "2025-01-01: 0.0433" in content
    assert "2026-01-01: 0.0371" in content
    assert "2031-01-01: 0.0230" in content
    assert "2025-01-01: 0.0280" in content
    assert "2026-01-01: 0.0240" in content
    assert (
        "OBR EFO March 2026 (detailed forecast tables, economy, Table 1.16)" in content
    )
    assert "https://obr.uk/efo/economic-and-fiscal-outlook-march-2026/" in content


def test_update_yoy_growth_yaml_keeps_existing_values_when_obr_has_blank_years(
    tmp_path,
):
    yaml_path = tmp_path / "yoy_growth.yaml"
    yaml_path.write_text("""obr:
  mortgage_interest:
    values:
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2027-01-01: 0.0553
    metadata:
      reference:
        - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.7)
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
  rpi:
    values:
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2027-01-01: 0.0000
    metadata:
      reference:
        - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.7)
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
  average_earnings:
    values:
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2027-01-01: 0.0000
    metadata:
      reference:
        - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.6)
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
  consumer_price_index:
    values:
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2027-01-01: 0.0000
    metadata:
      reference:
        - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.7)
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
  cpih:
    values:
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2027-01-01: 0.0000
    metadata:
      reference:
        - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.7)
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
  house_prices:
    values:
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2027-01-01: 0.0000
    metadata:
      reference:
        - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.16)
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
  rent:
    values:
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2027-01-01: 0.0000
    metadata:
      reference:
        - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.7)
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
""")

    update_yoy_growth_yaml(
        yaml_path=yaml_path,
        series_values=extract_annual_series_from_xlsx(make_test_xlsx()),
        month="March",
        year=2026,
        forecast_start_year=2025,
        forecast_years=3,
    )

    content = yaml_path.read_text()
    assert "2025-01-01: 0.0952" in content
    assert "2026-01-01: 0.0797" in content
    assert "2027-01-01: 0.0553" in content


def make_workbook(sheets: dict[str, bytes]) -> bytes:
    """An XLSX with the given sheets, in order."""
    names = list(sheets)
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        + "".join(
            f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>'
            for i, name in enumerate(names, start=1)
        )
        + "</sheets></workbook>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, len(names) + 1)
        )
        + "</Relationships>"
    )
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        for i, name in enumerate(names, start=1):
            archive.writestr(f"xl/worksheets/sheet{i}.xml", sheets[name])
    return buffer.getvalue()


def column_letter(index: int) -> str:
    return chr(ord("A") + index - 1)


def receipts_table(
    title: str,
    first_year: int,
    rows: list[tuple[str, tuple]],
    first_column: int = 3,
    outturn_years: int = 1,
) -> bytes:
    """A receipts table laid out as the OBR's: title in B2, the "Outturn"
    and "Forecast" markers in row 4 (each only where it has years), fiscal
    years in row 5, then one row per line (label in column B). Levels may be
    numbers or published cell text."""
    years = max(len(levels) for _, levels in rows)
    columns = [column_letter(first_column + i) for i in range(years)]
    sheet = {
        1: [make_inline_cell("A1", "Back to contents")],
        2: [make_inline_cell("B2", title)],
        3: [make_inline_cell(f"{columns[0]}3", "£ billion")],
        4: [
            *([make_inline_cell(f"{columns[0]}4", "Outturn")] if outturn_years else []),
            *(
                [make_inline_cell(f"{columns[outturn_years]}4", "Forecast")]
                if outturn_years < years
                else []
            ),
        ],
        5: [
            make_inline_cell(
                f"{column}5", f"{first_year + i}-{str(first_year + i + 1)[2:]}"
            )
            for i, column in enumerate(columns)
        ],
    }
    for row, (label, levels) in enumerate(rows, start=6):
        sheet[row] = [make_inline_cell(f"B{row}", label)] + [
            make_number_cell(f"{column}{row}", level)
            for column, level in zip(columns, levels)
        ]
    return make_sheet(sheet)


# Synthetic receipts, £bn, by property type and nation, from each EFO's
# first (outturn) year. Growth is checked against these by hand.
RECEIPTS_LEVELS = {
    "residential": (10.0, 11.0, 12.1),
    "non_residential": (4.0, 5.0, 4.5),
    "great_britain": (30.0, 31.5, 33.075),
    "northern_ireland": (0.4, 0.41, 0.4182),
}
PREVIOUS_RECEIPTS_LEVELS = {
    "residential": (8.0, 9.9, 10.5),
    "non_residential": (3.2, 3.0, 3.1),
    "great_britain": (29.0, 30.1, 31.0),
    "northern_ireland": (0.39, 0.395, 0.4),
}
# Synthetic betting and gaming duty receipts, £bn, from the year after each
# EFO's first (outturn) year, as the OBR's forecast breakdown starts. Remote
# Gaming Duty doubles in 2026-27 (2.8 = 1.4 x 40% / 21% x 1.05), when its
# rate rises from 21% to 40%, so its base grows 5%.
GAMBLING_LEVELS = {
    "remote_gaming": (1.4, 2.8, 2.94),
    "lottery": (1.0, 1.05, 1.1),
    "general_betting": (0.7, 0.72, 0.9),
    "machine_games": (0.65, 0.66, 0.8),
    "gaming": (0.17, 0.18, 0.19),
    "bingo": (0.03, 0.0001, 0.0),
    "pool_betting": (0.004, 0.0042, 0.0044),
}
GAMBLING_LABELS = {
    "remote_gaming": "Remote gaming duty",
    "lottery": "Lottery duty",
    "general_betting": "General betting duty",
    "machine_games": "Machine games duty",
    "gaming": "Gaming duty",
    "bingo": "Bingo duty",
    "pool_betting": "Pool betting duty",
}


def make_receipts_xlsx(
    release: str | None = "March 2026",
    first_year: int = 2024,
    levels: dict[str, tuple] | None = None,
    cash_table: str = "3.8",
    northern_ireland_label: str = "Northern Ireland business rates",
    outturn_years: int = 1,
    sdlt_rows: list[tuple[str, tuple]] | None = None,
    chapter: int = 3,
    gambling_levels: dict[str, tuple] | None = None,
) -> bytes:
    """Receipts tables numbered in ``chapter``: 3 to March 2026, 4 from
    October 2026."""
    levels = levels or RECEIPTS_LEVELS
    gambling_levels = gambling_levels or GAMBLING_LEVELS
    sheet_318 = make_sheet({2: [make_inline_cell("B2", "Other table")]})
    sheet_319 = make_sheet(
        {
            # An earlier table on the same sheet, with other years.
            2: [
                make_inline_cell("C2", "2020-21"),
                make_inline_cell("D2", "2021-22"),
            ],
            4: [
                make_inline_cell("C4", "2026-27"),
                make_inline_cell("D4", "2027-28"),
            ],
            21: [
                make_inline_cell("B21", "Memo: CPI used to uprate thresholds"),
                make_number_cell("C21", 3.81),
                make_number_cell("D21", 2.12),
            ],
        }
    )
    sheets = {}
    if release is not None:
        sheets["Contents"] = make_sheet(
            {
                2: [
                    make_inline_cell(
                        "B2",
                        f"{release} Economic and fiscal outlook – detailed "
                        "forecast tables: receipts",
                    )
                ],
                # The contents list names tables but holds none of their rows.
                6: [make_inline_cell("B6", f"{chapter}.2 Other taxes")],
            }
        )
    sheets[f"{chapter}.2"] = receipts_table(
        f"{chapter}.2 Other taxes",
        first_year,
        [
            (
                "Northern Ireland domestic rates",
                (0.5,) * len(levels["northern_ireland"]),
            ),
            (northern_ireland_label, levels["northern_ireland"]),
            ("Other taxes1", (12.0,) * len(levels["northern_ireland"])),
        ],
        outturn_years=outturn_years,
    )
    sheets[f"{chapter}.7"] = receipts_table(
        f"{chapter}.7 Property transactions taxes: Receipts by sector",
        first_year,
        sdlt_rows
        if sdlt_rows is not None
        else [
            (
                "Total SDLT",
                tuple(
                    r + n
                    for r, n in zip(levels["residential"], levels["non_residential"])
                ),
            ),
            ("SDLT from residential property", levels["residential"]),
            ("SDLT from non-residential property", levels["non_residential"]),
        ],
        outturn_years=outturn_years,
    )
    # An accrued table with a "Business rates" row of its own, which the
    # cash-basis series must not read.
    sheets[f"{chapter}.5"] = receipts_table(
        f"{chapter}.5 Current receipts (on an accrued basis)",
        first_year,
        [("Business rates", (99.0,) * len(levels["great_britain"]))],
        outturn_years=outturn_years,
    )
    sheets[cash_table] = receipts_table(
        f"{cash_table} Current receipts (on a cash basis)",
        first_year,
        [
            ("Stamp duty land tax", (14.0,) * len(levels["great_britain"])),
            ("Business rates", levels["great_britain"]),
            ("Council tax", (46.0,) * len(levels["great_britain"])),
        ],
        first_column=4,
        outturn_years=outturn_years,
    )
    # The betting and gaming breakdown publishes forecasts only, from the
    # year after the outturn year, under a total and an "of which" row.
    sheets[f"{chapter}.10"] = receipts_table(
        f"{chapter}.10 Betting and gaming duties forecast breakdown",
        first_year + 1,
        [
            (
                "Betting and gaming duties",
                tuple(
                    sum(float(level) for level in year)
                    for year in zip(*gambling_levels.values())
                ),
            ),
            ("of which:", ()),
            *((GAMBLING_LABELS[key], gambling_levels[key]) for key in GAMBLING_LABELS),
        ],
        outturn_years=0,
    )
    sheets[f"{chapter}.18"] = sheet_318
    sheets[f"{chapter}.19"] = sheet_319
    return make_workbook(sheets)


def make_previous_receipts_xlsx(**overrides) -> bytes:
    """The EFO before: outturn a year earlier, current receipts in Table 3.9
    and the Northern Ireland label in title case, as in March 2025."""
    return make_receipts_xlsx(
        **{
            "release": "March 2025",
            "first_year": 2023,
            "levels": PREVIOUS_RECEIPTS_LEVELS,
            "cash_table": "3.9",
            "northern_ireland_label": "Northern Ireland Business Rates",
            **overrides,
        }
    )


def test_september_cpi_is_keyed_to_the_september_before_the_uprating_year():
    table, rates = extract_september_cpi_from_receipts(make_receipts_xlsx())

    assert table == "3.19"
    assert rates == {2025: 0.0381, 2026: 0.0212}


def test_statutory_forecast_gaps_use_the_statutory_quarter():
    gaps = compute_statutory_forecast_gaps(make_test_xlsx(), 2025, 2)

    # Q3 CPI 2.08% minus calendar-year 2.48%; no 2025 quarter in the fixture.
    assert {y: g.value for y, g in gaps["cpi_september"].items()} == {2026: -0.004}
    # Q2 earnings 3.67% minus calendar-year 3.33%.
    assert {y: g.value for y, g in gaps["awe_total_pay_may_july"].items()} == {
        2026: 0.0034
    }


def test_statutory_forecast_gaps_prefer_published_september_cpi():
    gaps = compute_statutory_forecast_gaps(
        make_test_xlsx(), 2025, 2, receipts_xlsx_bytes=make_receipts_xlsx()
    )

    # September 2025 (3.81%) minus calendar-year 2025 CPI (3.45%), and
    # September 2026 (2.12%) minus calendar-year 2026 CPI (2.48%).
    cpi = gaps["cpi_september"]
    assert {y: g.value for y, g in cpi.items()} == {2025: 0.0036, 2026: -0.0036}
    assert "receipts Table 3.19" in cpi[2026].source


def test_update_forecast_gap_yaml_rewrites_values_and_reference(tmp_path):
    yaml_path = tmp_path / "cpi_september.yaml"
    yaml_path.write_text("""description: Gap.
values:
  2010-09-01: 0
  2025-09-01: 0.001
  2031-09-01: 0
metadata:
  unit: /1
  documentation: |
    Kept.
  reference:
    - title: OBR EFO November 2025 (detailed forecast tables, economy, Table 1.7)
      href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
""")
    spec = next(s for s in STATUTORY_GAP_SPECS if s.key == "cpi_september")
    gaps = compute_statutory_forecast_gaps(
        make_test_xlsx(), 2025, 2, receipts_xlsx_bytes=make_receipts_xlsx()
    )["cpi_september"]

    update_forecast_gap_yaml(yaml_path, spec, gaps, "March", 2026)

    content = yaml_path.read_text()
    assert "2025-09-01: 0.0036" in content
    assert "2026-09-01: -0.0036" in content
    assert "2027-09-01: 0" in content
    assert "0.001" not in content
    assert "Kept." in content
    assert "November 2025" not in content
    assert (
        "OBR EFO March 2026 (detailed forecast tables, economy, Table 1.7)" in content
    )
    assert (
        "OBR EFO March 2026 (detailed forecast tables, receipts, Table 3.19)" in content
    )
    assert "https://obr.uk/efo/economic-and-fiscal-outlook-march-2026/" in content


def test_gaps_are_measured_from_the_stored_calendar_growth():
    """Stored growth plus the gap must equal the OBR figure, so the gap is
    taken from whatever yoy_growth.yaml holds, not the unrounded workbook."""
    gaps = compute_statutory_forecast_gaps(
        make_test_xlsx(),
        2026,
        1,
        calendar_values={
            "consumer_price_index": {2026: 0.025},
            "average_earnings": {2026: 0.033},
        },
    )
    assert gaps["cpi_september"][2026].value == pytest.approx(0.0208 - 0.025)
    assert gaps["awe_total_pay_may_july"][2026].value == pytest.approx(0.0367 - 0.033)


def test_read_calendar_values(tmp_path):
    path = tmp_path / "yoy_growth.yaml"
    path.write_text(YOY_GROWTH_FIXTURE)
    values = read_calendar_values(path)
    assert values["consumer_price_index"] == {
        2024: 0.02,
        2025: 0.0,
        2026: 0.0,
        2031: 0.02,
    }


@pytest.mark.parametrize(
    "value, text",
    [
        (3e-05, "0.00003"),
        (-4e-05, "-0.00004"),
        (0.0003, "0.0003"),
        (0.0, "0"),
        (-0.00184, "-0.00184"),
    ],
)
def test_small_gaps_are_written_in_fixed_point(value, text):
    """YAML 1.1 reads 3e-05 as a string, which breaks parameter loading."""
    assert format_gap(value) == text
    spec = next(s for s in STATUTORY_GAP_SPECS if s.key == "cpi_september")
    content = render_forecast_gap_yaml(
        GAP_FIXTURE, spec, {2027: ForecastGap(value, "test", "test")}, "March", 2026
    )
    assert isinstance(yaml.safe_load(content)["values"][date(2027, 9, 1)], (int, float))


SERIES_KEYS = [
    "rpi",
    "average_earnings",
    "consumer_price_index",
    "cpih",
    "house_prices",
    "mortgage_interest",
    "rent",
]
FLAT_SERIES_FIXTURE = """  {key}:
    values:
      2024-01-01: 0.0200
      2025-01-01: 0.0000
      2026-01-01: 0.0000
      2031-01-01: 0.0200
    metadata:
      reference:
        - title: Old
          href: https://example.com/old
"""
RECEIPTS_SERIES_FIXTURE = """    {key}:
      description: {key} receipts growth.
      values:
        # Outturn (2023-24 over 2022-23), from an older EFO
        2023-01-01: 0.0500
        # Older forecast
        2024-01-01: 0.0100
        2025-01-01: 0.0100
        2031-01-01: 0.0200
      metadata:
        unit: /1
        label: {key} receipts growth
        reference:
          - title: Old
            href: https://example.com/old
"""
RECEIPTS_FIXTURE = (
    "\n  # Receipts growth; this comment and the blank lines around it stay.\n"
    "  stamp_duty_land_tax:\n"
    + RECEIPTS_SERIES_FIXTURE.format(key="residential")
    + RECEIPTS_SERIES_FIXTURE.format(key="non_residential")
    + "  business_rates:\n"
    + RECEIPTS_SERIES_FIXTURE.format(key="great_britain")
    + RECEIPTS_SERIES_FIXTURE.format(key="northern_ireland")
    + "  gambling_duty_bases:\n"
    + "".join(
        RECEIPTS_SERIES_FIXTURE.format(key=key)
        for key in (
            "remote_gaming",
            "lottery",
            "general_betting",
            "machine_games",
            "gaming",
            "bingo",
            "pool_betting",
        )
    )
    + "\n"
)
YOY_GROWTH_FIXTURE = (
    "obr:\n"
    + "".join(FLAT_SERIES_FIXTURE.format(key=key) for key in SERIES_KEYS[:2])
    + RECEIPTS_FIXTURE
    + "".join(FLAT_SERIES_FIXTURE.format(key=key) for key in SERIES_KEYS[2:])
    + """ons:
  population:
    values:
      2024-01-01: 0.0100
"""
)
GAP_FIXTURE = """description: Gap.
values:
  2010-09-01: 0
metadata:
  unit: /1
  reference:
    - title: Old
      href: https://example.com/old
"""


def write_tree(tmp_path):
    """A yoy_growth.yaml with the forecast_gap files next to it."""
    yoy = tmp_path / "economic_assumptions" / "yoy_growth.yaml"
    gap_dir = yoy.parent / "statutory_uprating_inputs" / "forecast_gap"
    gap_dir.mkdir(parents=True)
    yoy.write_text(YOY_GROWTH_FIXTURE)
    for spec in STATUTORY_GAP_SPECS:
        (gap_dir / f"{spec.key}.yaml").write_text(
            GAP_FIXTURE.replace("09-01", spec.month_day)
        )
    return yoy, gap_dir


def run_main(
    tmp_path, workbook, *extra, receipts=None, previous_receipts=None, previous=True
):
    economy = tmp_path / "economy_march_2026.xlsx"
    economy.write_bytes(workbook)
    receipts_path = tmp_path / "receipts.xlsx"
    receipts_path.write_bytes(receipts or make_receipts_xlsx())
    previous_path = tmp_path / "previous_receipts.xlsx"
    previous_path.write_bytes(previous_receipts or make_previous_receipts_xlsx())
    return main(
        [
            "--file",
            str(economy),
            "--forecast-start-year",
            "2025",
            "--forecast-years",
            "2",
            "--release-month",
            "March",
            "--release-year",
            "2026",
            "--receipts-file",
            str(receipts_path),
            *(["--previous-receipts-file", str(previous_path)] if previous else []),
            *extra,
        ]
    )


def test_main_writes_growth_and_gaps_next_to_the_yaml_path(tmp_path):
    yoy, gap_dir = write_tree(tmp_path)
    assert run_main(tmp_path, make_test_xlsx(), "--yaml-path", str(yoy)) == 0

    assert "2026-01-01: 0.0248" in yoy.read_text()
    cpi = yaml.safe_load((gap_dir / "cpi_september.yaml").read_text())["values"]
    # September 2026 (2.12%) minus the 2026 CPI just written (2.48%).
    assert cpi[date(2026, 9, 1)] == pytest.approx(-0.0036)
    awe = yaml.safe_load((gap_dir / "awe_total_pay_may_july.yaml").read_text())
    assert awe["values"][date(2026, 7, 1)] == pytest.approx(0.0034)


def test_main_writes_nothing_when_a_gap_cannot_be_built(tmp_path):
    """Without the Q2 earnings row there is no earnings gap: the run fails
    before any file changes, so growth and gaps never mix two forecasts."""
    yoy, gap_dir = write_tree(tmp_path)
    before = {path: path.read_text() for path in [yoy, *gap_dir.iterdir()]}

    with pytest.raises(ValueError, match="No forecast gaps"):
        run_main(
            tmp_path, make_test_xlsx(earnings_quarter=False), "--yaml-path", str(yoy)
        )

    assert {path: path.read_text() for path in before} == before


def test_main_requires_the_receipts_tables_for_the_gaps(tmp_path):
    yoy, _ = write_tree(tmp_path)
    economy = tmp_path / "economy_march_2026.xlsx"
    economy.write_bytes(make_test_xlsx())
    with pytest.raises(ValueError, match="receipts"):
        main(["--file", str(economy), "--yaml-path", str(yoy)])


def test_gaps_only_leaves_growth_alone(tmp_path):
    yoy, gap_dir = write_tree(tmp_path)
    growth = yoy.read_text()
    assert (
        run_main(
            tmp_path,
            make_test_xlsx(),
            "--yaml-path",
            str(yoy),
            "--gaps-only",
            previous=False,
        )
        == 0
    )

    assert yoy.read_text() == growth
    cpi = yaml.safe_load((gap_dir / "cpi_september.yaml").read_text())["values"]
    # September 2026 (2.12%) minus the stored 2026 CPI (0%).
    assert cpi[date(2026, 9, 1)] == pytest.approx(0.0212)


@pytest.mark.parametrize("failing_call", [1, 2, 3])
def test_main_restores_every_file_when_a_write_fails(
    tmp_path, monkeypatch, failing_call
):
    """A failure while moving the second or third file into place (or the
    first) leaves growth and both gap files exactly as they were."""
    yoy, gap_dir = write_tree(tmp_path)
    before = {path: path.read_text() for path in [yoy, *gap_dir.iterdir()]}
    real_replace = os.replace
    calls = []

    def flaky_replace(source, target):
        calls.append(target)
        if len(calls) == failing_call:
            raise OSError("disk full")
        real_replace(source, target)

    monkeypatch.setattr(import_obr_forecasts.os, "replace", flaky_replace)
    with pytest.raises(OSError, match="disk full"):
        run_main(tmp_path, make_test_xlsx(), "--yaml-path", str(yoy))

    assert {path: path.read_text() for path in before} == before
    leftovers = [*tmp_path.rglob("*.staged"), *tmp_path.rglob("*.backup")]
    assert leftovers == []


def test_main_leaves_files_alone_when_staging_fails(tmp_path, monkeypatch):
    yoy, gap_dir = write_tree(tmp_path)
    before = {path: path.read_text() for path in [yoy, *gap_dir.iterdir()]}
    real_write_text = Path.write_text
    staged = []

    def flaky_write_text(self, *args, **kwargs):
        if self.name.endswith(".staged"):
            staged.append(self)
            if len(staged) == 2:
                raise OSError("disk full")
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", flaky_write_text)
    with pytest.raises(OSError, match="disk full"):
        run_main(tmp_path, make_test_xlsx(), "--yaml-path", str(yoy))

    assert {path: path.read_text() for path in before} == before
    assert [*tmp_path.rglob("*.staged"), *tmp_path.rglob("*.backup")] == []


def test_a_failed_restore_keeps_the_original_and_never_empties_a_file(
    tmp_path, monkeypatch
):
    """The third move fails and so does the first restore. No file may be
    left empty: the unrestored file keeps the new text, its original is kept
    in a backup named in the error, and the other file is restored."""
    yoy, gap_dir = write_tree(tmp_path)
    before = {path: path.read_text() for path in [yoy, *gap_dir.iterdir()]}
    real_replace = os.replace
    calls = []

    def failing_replace(source, target):
        calls.append(target)
        if len(calls) in (3, 4):
            raise OSError("I/O error")
        real_replace(source, target)

    monkeypatch.setattr(import_obr_forecasts.os, "replace", failing_replace)
    with pytest.raises(OSError, match="original text is kept in") as error:
        run_main(tmp_path, make_test_xlsx(), "--yaml-path", str(yoy))

    unrestored = Path(calls[3])
    backup = unrestored.with_name(f".{unrestored.name}.backup")
    assert str(backup) in str(error.value)
    assert backup.read_text() == before[unrestored]
    for path, original in before.items():
        assert path.read_text(), path
        if path not in (unrestored, Path(calls[2])):
            assert path.read_text() == original, path
    assert list(tmp_path.rglob("*.staged")) == []


# Receipts growth series: stamp_duty_land_tax and business_rates under obr,
# which link their first year to the previous EFO's outturn, and the
# gambling_duty_bases, which grow a duty's base from HMRC's outturn.

RECEIPTS_SPECS = tuple(spec for spec in RECEIPTS_SERIES_SPECS if spec.outturn is None)
RECEIPTS_PATHS = {spec.path[-1]: spec.path for spec in RECEIPTS_SPECS}
GAMBLING_PATHS = {
    spec.path[-1]: spec.path
    for spec in RECEIPTS_SERIES_SPECS
    if spec.outturn is not None
}
ALL_RECEIPTS_PATHS = {**RECEIPTS_PATHS, **GAMBLING_PATHS}


def _series(tree, path):
    node = tree["obr"]
    for key in path:
        node = node[key]
    return node


def _values(content, path):
    return {
        instant.year: value
        for instant, value in _series(yaml.safe_load(content), path)["values"].items()
    }


def _in_effect(values, year):
    return values[max(y for y in values if y <= year)]


def render(content=YOY_GROWTH_FIXTURE, current=None, previous=None, **releases):
    growth = compute_receipts_growth(
        current or make_receipts_xlsx(), previous or make_previous_receipts_xlsx()
    )
    return render_receipts_growth_yaml(
        content,
        growth,
        releases.get("release", ("March", 2026)),
        releases.get("previous_release", ("March", 2025)),
    )


def test_receipts_lines_are_found_by_title_and_label_not_table_number():
    current = read_workbook_sheets(make_receipts_xlsx())
    previous = read_workbook_sheets(make_previous_receipts_xlsx())
    tables = {
        spec.path: (
            find_receipts_line(current, spec),
            find_receipts_line(previous, spec),
        )
        for spec in RECEIPTS_SPECS
    }

    great_britain, great_britain_before = tables[RECEIPTS_PATHS["great_britain"]]
    # Current receipts on a cash basis move from 3.9 to 3.8; the accrued
    # table's own "Business rates" row is ignored.
    assert (great_britain.table, great_britain_before.table) == ("3.8", "3.9")
    assert great_britain.levels == {2024: 30.0, 2025: 31.5, 2026: 33.075}
    northern_ireland, northern_ireland_before = tables[
        RECEIPTS_PATHS["northern_ireland"]
    ]
    assert northern_ireland.label == "Northern Ireland business rates"
    assert northern_ireland_before.label == "Northern Ireland Business Rates"
    assert northern_ireland_before.levels[2023] == 0.39
    for line, line_before in tables.values():
        assert line.outturn_years == {2024}
        assert line_before.outturn_years == {2023}


def test_receipts_growth_is_the_ratio_of_published_levels():
    growth = compute_receipts_growth(
        make_receipts_xlsx(), make_previous_receipts_xlsx()
    )
    # The first year is this EFO's outturn over the previous EFO's outturn,
    # e.g. residential 10.0 / 8.0; later years are this EFO's own ratios.
    assert {
        path[-1]: series.values
        for path, series in growth.items()
        if path in RECEIPTS_PATHS.values()
    } == {
        "residential": {2024: 0.25, 2025: 0.1, 2026: 0.1},
        "non_residential": {2024: 0.25, 2025: 0.25, 2026: -0.1},
        "great_britain": {2024: 0.034483, 2025: 0.05, 2026: 0.05},
        "northern_ireland": {2024: 0.025641, 2025: 0.025, 2026: 0.02},
    }


def test_the_previous_efo_must_publish_outturn_for_the_base_year():
    # An EFO whose first outturn year is 2022-23 has 2023-24 as a forecast.
    two_years_back = make_previous_receipts_xlsx(first_year=2022)
    with pytest.raises(ValueError, match="no 2023-24 outturn"):
        compute_receipts_growth(make_receipts_xlsx(), two_years_back)
    # An EFO from the same outturn year has no 2023-24 at all.
    with pytest.raises(ValueError, match="no 2023-24 outturn"):
        compute_receipts_growth(make_receipts_xlsx(), make_receipts_xlsx())


def test_the_first_year_must_be_outturn():
    no_outturn = make_receipts_xlsx(outturn_years=0)
    with pytest.raises(
        ValueError,
        match="residential: 2024-25, the first year in Table 3.7, is not outturn",
    ):
        compute_receipts_growth(no_outturn, make_previous_receipts_xlsx())


@pytest.mark.parametrize(
    "sdlt_rows, message",
    [
        ([("SDLT from non-residential property", (4.0, 5.0, 4.5))], "found none"),
        (
            [
                ("SDLT from residential property", (10.0, 11.0, 12.1)),
                ("SDLT from residential property", (10.0, 11.0, 12.1)),
                ("SDLT from non-residential property", (4.0, 5.0, 4.5)),
            ],
            "found sheet 3.7, sheet 3.7",
        ),
    ],
)
def test_each_receipts_line_must_appear_exactly_once(sdlt_rows, message):
    with pytest.raises(ValueError, match=message):
        compute_receipts_growth(
            make_receipts_xlsx(sdlt_rows=sdlt_rows), make_previous_receipts_xlsx()
        )


def test_receipts_growth_rejects_a_missing_or_non_positive_level():
    missing = make_receipts_xlsx(
        sdlt_rows=[
            ("SDLT from residential property", (10.0, 11.0)),
            ("SDLT from non-residential property", (4.0, 5.0, 4.5)),
        ]
    )
    with pytest.raises(ValueError, match="no numeric 2026-27 .* value: None"):
        compute_receipts_growth(missing, make_previous_receipts_xlsx())
    zero = make_receipts_xlsx(
        sdlt_rows=[
            ("SDLT from residential property", (10.0, 0.0, 12.1)),
            ("SDLT from non-residential property", (4.0, 5.0, 4.5)),
        ]
    )
    with pytest.raises(ValueError, match="2025-26 receipts of 0.0 are not positive"):
        compute_receipts_growth(zero, make_previous_receipts_xlsx())


@pytest.mark.parametrize("last", [0.0, -1.0])
def test_a_last_level_at_or_below_zero_is_refused(last):
    # Growth of -100% or less would zero (or flip) the index from then on.
    levels = make_receipts_xlsx(
        sdlt_rows=[
            ("SDLT from residential property", (10.0, 11.0, last)),
            ("SDLT from non-residential property", (4.0, 5.0, 4.5)),
        ]
    )
    with pytest.raises(
        ValueError, match=f"2026-27 receipts of {last} are not positive"
    ):
        compute_receipts_growth(levels, make_previous_receipts_xlsx())


def test_receipts_labels_lose_footnote_markers_only():
    line = find_receipts_line(
        read_workbook_sheets(
            make_receipts_xlsx(
                sdlt_rows=[
                    ("SDLT from residential property2", (10.0, 11.0, 12.1)),
                    ("SDLT from non-residential property", (4.0, 5.0, 4.5)),
                ]
            )
        ),
        RECEIPTS_SERIES_SPECS[0],
    )
    assert line.label == "SDLT from residential property"


def test_a_non_numeric_level_is_refused():
    text = make_receipts_xlsx(
        sdlt_rows=[
            ("SDLT from residential property", (10.0, "[x]", 12.1)),
            ("SDLT from non-residential property", (4.0, 5.0, 4.5)),
        ]
    )
    with pytest.raises(ValueError, match="no numeric 2025-26 .* value: '\\[x\\]'"):
        compute_receipts_growth(text, make_previous_receipts_xlsx())


CASH_TITLE = "3.8 Current receipts (on a cash basis)"
GREAT_BRITAIN = next(
    spec for spec in RECEIPTS_SERIES_SPECS if spec.path[-1] == "great_britain"
)


def cash_table_rows(*, markers=None, years=None, label="Business rates"):
    """Rows of a cash-basis receipts table as read_workbook_sheets returns
    them: title, markers, fiscal years, then one line."""
    return [
        {"B": CASH_TITLE},
        {"D": "£ billion"},
        *(markers or [{"D": "Outturn", "E": "Forecast"}]),
        years or {"D": "2024-25", "E": "2025-26", "F": "2026-27"},
        {"B": label, "D": "30", "E": "31.5", "F": "33.075"},
    ]


def test_a_line_is_read_only_from_its_own_table():
    # A cash-basis table without the line, then an accrued-basis table with
    # one, on the same sheet: the accrued line must not stand in for it.
    rows = [
        {"B": CASH_TITLE},
        {"D": "Outturn", "E": "Forecast"},
        {"D": "2024-25", "E": "2025-26", "F": "2026-27"},
        {"B": "Council tax", "D": "46", "E": "47", "F": "48"},
        {"B": "3.5 Current receipts (on an accrued basis)"},
        {"D": "Outturn", "E": "Forecast"},
        {"D": "2024-25", "E": "2025-26", "F": "2026-27"},
        {"B": "Business rates", "D": "99", "E": "100", "F": "101"},
    ]
    with pytest.raises(ValueError, match="found none"):
        find_receipts_line({"3.8": rows}, GREAT_BRITAIN)


def test_a_table_title_below_publication_notes_is_found():
    rows = [
        {"A": "Publication note"},
        {"A": "Another note"},
        {"A": "Back to contents"},
        *cash_table_rows(),
    ]
    line = find_receipts_line({"3.8": rows}, GREAT_BRITAIN)
    assert (line.table, line.levels) == ("3.8", {2024: 30, 2025: 31.5, 2026: 33.075})


def test_outturn_and_forecast_markers_may_sit_on_separate_rows():
    rows = cash_table_rows(markers=[{"E": "Forecast"}, {"D": "Outturn"}])
    line = find_receipts_line({"3.8": rows}, GREAT_BRITAIN)
    assert line.outturn_years == {2024}


def test_a_marker_in_two_columns_is_refused():
    rows = cash_table_rows(
        markers=[{"D": "Outturn", "E": "Forecast"}, {"E": "Outturn"}]
    )
    with pytest.raises(ValueError, match='marks "Outturn" in two different columns'):
        find_receipts_line({"3.8": rows}, GREAT_BRITAIN)


def test_a_fiscal_year_heading_two_columns_is_refused():
    rows = cash_table_rows(years={"D": "2024-25", "E": "2025-26", "F": "2025-26"})
    with pytest.raises(ValueError, match="heads more than one column 2025-26"):
        find_receipts_line({"3.8": rows}, GREAT_BRITAIN)


def test_render_rewrites_values_and_references():
    rendered = render()
    start = rendered.index("    residential:")
    end = rendered.index("    non_residential:")
    assert rendered[start:end] == (
        """    residential:
      description: residential receipts growth.
      values:
        # Outturn (2023-24 over 2022-23), from an older EFO
        2023-01-01: 0.0500
        # Outturn (2024-25 over 2023-24) from OBR EFO March 2026 over March 2025, receipts Table 3.7 "SDLT from residential property"
        2024-01-01: 0.2500
        # Forecast (2025-2026) from OBR EFO March 2026, receipts Table 3.7
        2025-01-01: 0.1000
        2026-01-01: 0.1000
        # Beyond the OBR forecast: the average_earnings long-run path above
        2027-01-01: 0.0000
        2031-01-01: 0.0200
      metadata:
        unit: /1
        label: residential receipts growth
        reference:
          - title: OBR EFO March 2026 (detailed forecast tables, receipts, Table 3.7)
            href: https://obr.uk/efo/economic-and-fiscal-outlook-march-2026/
          - title: OBR EFO March 2025 (detailed forecast tables, receipts, Table 3.7; 2023-24 outturn)
            href: https://obr.uk/efo/economic-and-fiscal-outlook-march-2025/
"""
    )
    assert (
        "# Outturn (2024-25 over 2023-24) from OBR EFO March 2026 over March 2025, "
        'receipts Table 3.8 (March 2025: Table 3.9) "Business rates"'
    ) in rendered
    assert "receipts, Table 3.9; 2023-24 outturn" in rendered


def test_render_changes_only_the_receipts_values_and_references():
    rendered = render()
    before, after = yaml.safe_load(YOY_GROWTH_FIXTURE), yaml.safe_load(rendered)
    for tree in (before, after):
        for path in ALL_RECEIPTS_PATHS.values():
            del _series(tree, path)["values"]
            del _series(tree, path)["metadata"]["reference"]
    assert after == before
    # Text outside the series' values and reference blocks is untouched.
    assert rendered.startswith(
        YOY_GROWTH_FIXTURE[: YOY_GROWTH_FIXTURE.index("    residential:")]
    )
    tail = YOY_GROWTH_FIXTURE[YOY_GROWTH_FIXTURE.index("\n  consumer_price_index:") :]
    assert rendered.endswith(tail)
    assert (
        "# Receipts growth; this comment and the blank lines around it stay."
        in rendered
    )


@pytest.mark.parametrize("indent", [0, 2, 4, 6, 8])
def test_a_comment_at_any_indent_ends_no_yaml_block(indent):
    comment = " " * indent + "# A comment before the values"
    anchor = "    residential:\n      description: residential receipts growth.\n"
    assert YOY_GROWTH_FIXTURE.count(anchor) == 1
    content = YOY_GROWTH_FIXTURE.replace(anchor, anchor + comment + "\n")
    assert yaml.safe_load(content) == yaml.safe_load(YOY_GROWTH_FIXTURE)

    rendered = render(content)

    assert anchor + comment + "\n      values:\n" in rendered
    assert rendered.replace(comment + "\n", "", 1) == render()


def test_render_is_idempotent():
    once = render()
    assert render(once) == once


def test_a_later_efo_keeps_the_years_before_its_outturn_year():
    """The next EFO's first year is 2025: 2024 keeps its value and comment,
    so each index keeps its base year."""
    march_2026 = render()
    march_2027 = render(
        march_2026,
        current=make_receipts_xlsx(
            release="March 2027",
            first_year=2025,
            levels={key: (11.0, 12.1, 13.31) for key in RECEIPTS_LEVELS},
        ),
        previous=make_receipts_xlsx(),
        release=("March", 2027),
        previous_release=("March", 2026),
    )
    path = RECEIPTS_PATHS["residential"]
    assert _values(march_2027, path) == {
        2023: 0.05,
        2024: 0.25,
        # 2025-26 outturn (11.0) over 2024-25 outturn in March 2026 (10.0).
        2025: 0.1,
        2026: 0.1,
        2027: 0.1,
        2028: 0.0,
        2031: 0.02,
    }
    assert (
        "# Outturn (2024-25 over 2023-24) from OBR EFO March 2026 over March 2025, "
        'receipts Table 3.7 "SDLT from residential property"\n'
        "        2024-01-01: 0.2500\n"
        "        # Outturn (2025-26 over 2024-25) from OBR EFO March 2027 over March 2026"
    ) in march_2027
    assert "March 2025 (detailed" not in march_2027


def test_later_outturn_years_get_their_own_comment():
    rendered = render(current=make_receipts_xlsx(outturn_years=2))
    assert (
        "# Outturn (2025) from OBR EFO March 2026, receipts Table 3.7\n"
        "        2025-01-01: 0.1000\n"
        "        # Forecast (2026) from OBR EFO March 2026, receipts Table 3.7\n"
    ) in rendered


def test_average_earnings_path_lists_each_change_after_the_forecast():
    content = """obr:
  average_earnings:
    values:
      2029-01-01: 0.022
      2030-01-01: 0.024
      2031-01-01: 0.0332
      2032-01-01: 0.0371
      2036-01-01: 0.0383
      2037-01-01: 0.0383
      2073-01-01: 0.0383
"""
    assert average_earnings_path(content, 2030) == {
        2031: 0.0332,
        2032: 0.0371,
        2036: 0.0383,
    }
    # Starting between entries takes the value then in effect.
    assert average_earnings_path(content, 2033) == {2034: 0.0371, 2036: 0.0383}
    with pytest.raises(ValueError, match="no value in effect in 2028"):
        average_earnings_path(content, 2027)


@pytest.mark.parametrize(
    "value, text",
    [
        (0.0383, "0.0383"),
        (0.038, "0.0380"),
        (0.1302, "0.1302"),
        (0.06083, "0.06083"),
        (0.211202, "0.211202"),
        (-0.1, "-0.1000"),
        (1e-05, "0.00001"),
        (-0.0, "0.0000"),
    ],
)
def test_growth_is_written_in_fixed_point(value, text):
    assert format_growth(value) == text


@settings(max_examples=300, deadline=None, derandomize=True)
@given(st.floats(min_value=-1, max_value=100, allow_nan=False))
def test_written_growth_reads_back_exactly(value):
    text = format_growth(value)
    assert "e" not in text.lower()
    assert len(text.partition(".")[2]) >= 4
    assert yaml.safe_load(f"x: {text}")["x"] == value


def test_read_calendar_values_includes_nested_series(tmp_path):
    path = tmp_path / "yoy_growth.yaml"
    path.write_text(YOY_GROWTH_FIXTURE)
    values = read_calendar_values(path)
    assert values["stamp_duty_land_tax.residential"] == {
        2023: 0.05,
        2024: 0.01,
        2025: 0.01,
        2031: 0.02,
    }
    assert set(values) == set(SERIES_KEYS) | {
        ".".join(path) for path in ALL_RECEIPTS_PATHS.values()
    }


LEVELS = st.floats(min_value=0.01, max_value=1_000, allow_nan=False)


@settings(max_examples=40, deadline=None, derandomize=True)
@given(
    years=st.integers(2, 8),
    data=st.data(),
)
def test_rendered_growth_compounds_the_published_levels(years, data):
    """For any published levels: every year from the outturn year is the
    six-decimal ratio of consecutive levels, every later year equals
    average_earnings, years before the outturn year are kept, and a second
    run changes nothing."""
    levels = {
        key: tuple(data.draw(st.lists(LEVELS, min_size=years, max_size=years)))
        for key in RECEIPTS_LEVELS
    }
    base = {key: (data.draw(LEVELS),) for key in RECEIPTS_LEVELS}
    current = make_receipts_xlsx(levels=levels)
    previous = make_previous_receipts_xlsx(levels=base)
    rendered = render(current=current, previous=previous)

    average_earnings = _values(rendered, ("average_earnings",))
    last = 2024 + years - 1
    for key, path in RECEIPTS_PATHS.items():
        values = _values(rendered, path)
        published = {
            2023: base[key][0],
            **dict(zip(range(2024, last + 1), levels[key])),
        }
        for year in range(2024, last + 1):
            expected = round(published[year] / published[year - 1] - 1, 6)
            assert values[year] == expected
        for year in range(last + 1, 2050):
            assert _in_effect(values, year) == _in_effect(average_earnings, year)
        assert values[2023] == 0.05
    assert render(rendered, current=current, previous=previous) == rendered


# Published OBR receipts levels as the workbooks hold them (£bn): the October
# 2026 EFO from 2025-26 and the March 2026 EFO from 2024-25.
OCTOBER_2026_RECEIPTS = {
    "residential": ("11.55444496305409", "11.598497804863152", "12.81121827423391", "14.275385542155488", "15.523034837312446", "16.708206755202507", "17.97120998332108"),
    "non_residential": ("3.6048001541859174", "3.4392848579522055", "4.060008995487192", "4.6692547224804075", "4.8746831796154595", "5.306606478148783", "5.725680069577546"),
    "great_britain": ("33.929814327646056", "35.43608032863263", "37.21735218338801", "38.66510919685915", "41.462982206056644", "42.42035811098974", "43.447399285510656"),
    "northern_ireland": ("0.3955394050104385", "0.40595301023058955", "0.414556055466312", "0.4226801104356366", "0.43095512116333085", "0.4394491849889923", "0.44783993918412923"),
}  # fmt: skip
# The October 2026 EFO's betting and gaming duties (£bn, Table 4.10) from
# 2026-27, which publishes forecasts only.
OCTOBER_2026_GAMBLING = {
    "remote_gaming": ("2.7520296250837784", "2.7812750734699425", "2.8416867878041874", "2.9053716896455919", "2.9446821891345443", "2.963204761653297"),
    "lottery": ("0.83052038459597621", "0.84965566898040046", "0.87574553838772884", "0.90350845044750805", "0.92958587301870155", "0.95685079671453654"),
    "general_betting": ("0.65560522982822456", "0.87744453968275893", "0.91694664204685206", "0.94862995017184315", "0.97646741817020943", "1.0041740187990271"),
    "machine_games": ("0.67707068705786499", "0.82692873727074745", "0.85695449075649544", "0.86524127517297356", "0.87550370868921701", "0.89631020781238802"),
    "gaming": ("0.17422987982556123", "0.18488058456996015", "0.18523427331264838", "0.18548069649974164", "0.18650974968911124", "0.18568125218312026"),
    "bingo": ("1.8867652000000002E-4", "0", "0", "0", "0", "0"),
    "pool_betting": ("2.8288821260900035E-3", "2.6802893699237468E-3", "2.85842704577818E-3", "2.8371447589557743E-3", "2.9959073747097458E-3", "3.1258296515431082E-3"),
}  # fmt: skip
MARCH_2026_RECEIPTS = {
    "residential": ("10.379999999999999", "11.731471524432562", "13.428906667032589", "14.984943814530874", "16.673948133476184", "17.964513468126285", "19.057301113969185"),
    "non_residential": ("3.5049999999999999", "3.6750451743530199", "4.72127759316189", "5.3288288104799904", "5.9009139798817092", "6.5330695355310402", "7.1046581772762902"),
    "great_britain": ("32.376814327646052", "34.051963932489258", "37.413586572144581", "38.240930947824609", "39.111850954748434", "42.419067764546902", "42.463193622519263"),
    "northern_ireland": ("0.38233350730688931", "0.39471664406441903", "0.40263364127921164", "0.41045270712298504", "0.41810894612429189", "0.42590403232705243", "0.43449009714292341"),
}  # fmt: skip


def test_october_2026_tables_reproduce_the_committed_series():
    """yoy_growth.yaml holds exactly what the importer writes from the
    October 2026 receipts tables (Tables 4.7, 4.8, 4.2 and 4.10) and the
    March 2026 ones (3.7, 3.8 and 3.2): rerunning it on the committed file
    changes nothing."""
    committed = get_yoy_growth_path().read_text()
    rendered = render(
        committed,
        current=make_receipts_xlsx(
            release="October 2026",
            first_year=2025,
            levels=OCTOBER_2026_RECEIPTS,
            cash_table="4.8",
            chapter=4,
            gambling_levels=OCTOBER_2026_GAMBLING,
        ),
        previous=make_previous_receipts_xlsx(
            release="March 2026",
            first_year=2024,
            levels=MARCH_2026_RECEIPTS,
            cash_table="3.8",
            northern_ireland_label="Northern Ireland business rates",
        ),
        release=("October", 2026),
        previous_release=("March", 2026),
    )
    assert rendered == committed


REAL_RECEIPTS_DIR = Path(__file__).parent / "fixtures" / "obr_receipts"
REAL_RECEIPTS = {
    year: (REAL_RECEIPTS_DIR / f"obr_efo_march_{year}_receipts.xlsx").read_bytes()
    for year in (2025, 2026)
}
REAL_OCTOBER_2026_RECEIPTS = (
    REAL_RECEIPTS_DIR / "obr_efo_october_2026_receipts.xlsx"
).read_bytes()
COMMITTED_RELEASES = {"release": ("October", 2026), "previous_release": ("March", 2026)}
XLSX_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_NS = {"m": XLSX_MAIN}


def mutate_real_receipts(workbook, table, unit, scale=1):
    """Change the real table's unit cell and scale its selected receipts rows.

    Keep all other archive entries, including the shared strings, unchanged.
    """
    output = BytesIO()
    with ZipFile(BytesIO(workbook)) as source, ZipFile(output, "w") as dest:
        path = _sheet_paths(source)[table]
        strings = [
            "".join(node.itertext())
            for node in ET.fromstring(source.read("xl/sharedStrings.xml"))
        ]
        sheet = ET.fromstring(source.read(path))
        first_column = "D" if table in ("3.8", "3.9", "4.8") else "C"
        cell = sheet.find(f"m:sheetData/m:row/m:c[@r='{first_column}3']", XLSX_NS)
        cell.clear()
        cell.attrib.update(r=f"{first_column}3", t="inlineStr")
        ET.SubElement(
            ET.SubElement(cell, f"{{{XLSX_MAIN}}}is"), f"{{{XLSX_MAIN}}}t"
        ).text = unit
        labels = {spec.row for spec in RECEIPTS_SERIES_SPECS}
        for row in sheet.findall("m:sheetData/m:row", XLSX_NS):
            label = row.find("m:c[@t='s']/m:v", XLSX_NS)
            if label is None or strings[int(label.text)].lower() not in labels:
                continue
            for number in row.findall("m:c", XLSX_NS):
                value = number.find("m:v", XLSX_NS)
                if value is not None and number.attrib.get("t") != "s":
                    value.text = repr(float(value.text) * scale)
        for entry in source.infolist():
            dest.writestr(
                entry,
                ET.tostring(sheet) if entry.filename == path else source.read(entry),
            )
    return output.getvalue()


def test_real_receipts_workbooks_reproduce_committed_yaml_byte_for_byte():
    committed = get_yoy_growth_path().read_bytes()
    rendered = render(
        committed.decode(),
        current=REAL_OCTOBER_2026_RECEIPTS,
        previous=REAL_RECEIPTS[2026],
        **COMMITTED_RELEASES,
    )
    assert rendered.encode() == committed


def test_october_2026_cash_receipts_cite_the_sheet_not_the_misprinted_title():
    # The October 2026 workbook titles sheet 4.8 "43.8 Current receipts (on a
    # cash basis)"; its contents sheet and sheet name say 4.8.
    growth = compute_receipts_growth(REAL_OCTOBER_2026_RECEIPTS, REAL_RECEIPTS[2026])
    assert growth[("business_rates", "great_britain")].line.table == "4.8"


@pytest.mark.parametrize(
    "year, tables", [(2026, ("3.2", "3.7", "3.8")), (2025, ("3.2", "3.7", "3.9"))]
)
@pytest.mark.parametrize(
    "unit, scale",
    [
        ("£ million", 1000),
        ("£m", 1000),
        ("% of GDP", 1),
        ("£ billion (real terms)", 1),
        ("£ billion per cent", 1),
        ("€ billion", 1),
        ("", 1),
    ],
)
def test_real_receipts_units_are_refused_before_any_write(
    tmp_path, year, tables, unit, scale
):
    for table in tables:
        yoy, gap_dir = write_tree(tmp_path / table)
        before = {path: path.read_bytes() for path in [yoy, *gap_dir.iterdir()]}
        receipts = dict(REAL_RECEIPTS)
        receipts[year] = mutate_real_receipts(receipts[year], table, unit, scale)
        with pytest.raises(ValueError, match=rf"Table {table} .*receipts unit"):
            run_main(
                tmp_path,
                make_test_xlsx(),
                "--yaml-path",
                str(yoy),
                receipts=receipts[2026],
                previous_receipts=receipts[2025],
            )
        assert {path: path.read_bytes() for path in before} == before
        assert not list(yoy.parent.rglob("*.staged"))


SUPPORTED_BILLION_LABELS = (
    "£ billion",
    "£bn",
    "£ bn",
    "  £ BILLION  ",
    "£\u00a0billion",
)


@pytest.mark.parametrize("unit", SUPPORTED_BILLION_LABELS)
def test_explicit_billion_unit_aliases_preserve_the_real_workbook_output(unit):
    assert (
        render(
            get_yoy_growth_path().read_text(),
            current=mutate_real_receipts(REAL_OCTOBER_2026_RECEIPTS, "4.8", unit),
            previous=mutate_real_receipts(REAL_RECEIPTS[2026], "3.8", unit),
            **COMMITTED_RELEASES,
        ).encode()
        == get_yoy_growth_path().read_bytes()
    )


@pytest.mark.parametrize(
    "declarations",
    [[], [{"D": "£ billion"}, {"D": "£ million"}], [{"D": "£ billion", "E": "% GDP"}]],
)
def test_receipts_units_must_be_unambiguous_and_belong_to_the_selected_table(
    declarations,
):
    rows = cash_table_rows()
    rows[1:2] = declarations
    # A valid unit in another table must not supply a missing cash-table unit.
    rows += [{"B": "3.5 Current receipts (on an accrued basis)"}, {"D": "£ billion"}]
    with pytest.raises(ValueError, match="receipts unit"):
        find_receipts_line({"3.8": rows}, GREAT_BRITAIN)


@settings(max_examples=50, deadline=None, derandomize=True)
@given(
    current_unit=st.one_of(
        st.sampled_from(SUPPORTED_BILLION_LABELS),
        st.sampled_from(
            ("£m", "£ million", "£ billion per cent", "% GDP", "USD billion", "")
        ),
        st.text(
            alphabet="£€$%abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./()-_",
            max_size=30,
        ),
    ),
    previous_unit=st.sampled_from((*SUPPORTED_BILLION_LABELS, "£m", "€ billion", "")),
    scale=st.floats(
        min_value=0.001, max_value=1000, allow_nan=False, allow_infinity=False
    ),
)
def test_real_receipts_unit_labels_and_scale_factors(
    current_unit, previous_unit, scale
):
    """A common scale cannot change ratios; unsupported declarations always fail."""
    current = mutate_real_receipts(REAL_RECEIPTS[2026], "3.8", current_unit, scale)
    previous = mutate_real_receipts(REAL_RECEIPTS[2025], "3.9", previous_unit, scale)
    supported = {"£ billion", "£bn", "£ bn"}
    if any(
        " ".join(unit.lower().split()) not in supported
        for unit in (current_unit, previous_unit)
    ):
        with pytest.raises(ValueError, match="receipts unit"):
            compute_receipts_growth(current, previous)
    else:
        expected = compute_receipts_growth(REAL_RECEIPTS[2026], REAL_RECEIPTS[2025])
        actual = compute_receipts_growth(current, previous)
        assert {path: series.values for path, series in actual.items()} == {
            path: series.values for path, series in expected.items()
        }


def test_next_release_real_receipts_refuse_a_thousandfold_unit_change():
    """The review's next-EFO attack must never turn zero growth into 999."""
    output = BytesIO()
    with ZipFile(BytesIO(REAL_RECEIPTS[2026])) as source, ZipFile(output, "w") as dest:
        # Shift only the release and year labels in the original shared strings,
        # retaining every numeric cell and the worksheets' original layout.
        path = "xl/sharedStrings.xml"
        strings = ET.fromstring(source.read(path))
        for text in strings.iter(f"{{{XLSX_MAIN}}}t"):
            if text.text and import_obr_forecasts.FISCAL_YEAR_RE.fullmatch(text.text):
                text.text = import_obr_forecasts.fiscal_year_label(
                    int(text.text[:4]) + 1
                )
            elif text.text:
                text.text = text.text.replace("March 2026", "March 2027")
        for entry in source.infolist():
            dest.writestr(
                entry,
                ET.tostring(strings) if entry.filename == path else source.read(entry),
            )
    advanced = output.getvalue()
    assert infer_workbook_release(advanced) == ("March", 2027)
    control = compute_receipts_growth(advanced, REAL_RECEIPTS[2026])
    assert control[RECEIPTS_PATHS["great_britain"]].values[2025] == 0.0
    attacked = mutate_real_receipts(advanced, "3.8", "£m", 1000)
    with pytest.raises(ValueError, match="receipts unit"):
        compute_receipts_growth(attacked, REAL_RECEIPTS[2026])


def test_workbook_release_comes_from_the_contents_sheet():
    assert infer_workbook_release(make_receipts_xlsx()) == ("March", 2026)
    assert infer_workbook_release(make_receipts_xlsx(release=None)) is None
    assert infer_workbook_release(make_test_xlsx()) is None


def test_main_updates_receipts_growth_from_the_new_average_earnings(tmp_path):
    yoy, _ = write_tree(tmp_path)
    assert run_main(tmp_path, make_test_xlsx(), "--yaml-path", str(yoy)) == 0

    content = yoy.read_text()
    assert _values(content, RECEIPTS_PATHS["great_britain"]) == {
        2023: 0.05,
        2024: 0.034483,
        2025: 0.05,
        2026: 0.05,
        # 2026 average earnings as this run writes it, then the long run.
        2027: 0.0333,
        2031: 0.02,
    }
    assert "2026-01-01: 0.0333" in content


def test_main_requires_the_previous_receipts_tables(tmp_path):
    yoy, gap_dir = write_tree(tmp_path)
    before = {path: path.read_text() for path in [yoy, *gap_dir.iterdir()]}
    with pytest.raises(ValueError, match="--skip-receipts-growth"):
        run_main(tmp_path, make_test_xlsx(), "--yaml-path", str(yoy), previous=False)
    assert {path: path.read_text() for path in before} == before

    assert (
        run_main(
            tmp_path,
            make_test_xlsx(),
            "--yaml-path",
            str(yoy),
            "--skip-receipts-growth",
            previous=False,
        )
        == 0
    )
    content = yoy.read_text()
    assert "2026-01-01: 0.0248" in content
    for path in ALL_RECEIPTS_PATHS.values():
        assert _values(content, path) == _values(YOY_GROWTH_FIXTURE, path)


def test_main_dry_run_without_previous_receipts_only_warns(tmp_path, capsys):
    yoy, _ = write_tree(tmp_path)
    assert (
        run_main(
            tmp_path,
            make_test_xlsx(),
            "--yaml-path",
            str(yoy),
            "--dry-run",
            previous=False,
        )
        == 0
    )
    assert "Warning: Pass the receipts tables" in capsys.readouterr().out
    assert yoy.read_text() == YOY_GROWTH_FIXTURE


@pytest.mark.parametrize(
    "receipts, previous_receipts, message",
    [
        (
            make_receipts_xlsx(release="November 2025"),
            None,
            "receipts tables are from November 2025 but the economy tables are "
            "from March 2026",
        ),
        (
            None,
            make_previous_receipts_xlsx(release="March 2026"),
            r"previous receipts tables \(March 2026\) must come from an EFO "
            "before March 2026",
        ),
        (
            None,
            make_previous_receipts_xlsx(release=None),
            "Could not tell which EFO the previous receipts tables are from",
        ),
        # No contents sheet and a file name without a release: the growth
        # would otherwise be written from tables of an unknown EFO.
        (
            make_receipts_xlsx(release=None),
            None,
            "Could not tell which EFO the receipts tables are from",
        ),
    ],
    ids=[
        "receipts_from_another_efo",
        "previous_not_earlier",
        "previous_unidentified",
        "receipts_unidentified",
    ],
)
def test_main_refuses_tables_from_the_wrong_efo(
    tmp_path, receipts, previous_receipts, message
):
    yoy, gap_dir = write_tree(tmp_path)
    before = {path: path.read_text() for path in [yoy, *gap_dir.iterdir()]}
    with pytest.raises(ValueError, match=message):
        run_main(
            tmp_path,
            make_test_xlsx(),
            "--yaml-path",
            str(yoy),
            receipts=receipts,
            previous_receipts=previous_receipts,
        )
    assert {path: path.read_text() for path in before} == before


def rebuild_workbook(xlsx_bytes, *, drop=(), first=None):
    """The workbook without the ``drop`` sheets, with ``first`` sheets
    (name to sheet XML) in front."""
    with ZipFile(BytesIO(xlsx_bytes)) as archive:
        sheets = {
            name: archive.read(path)
            for name, path in _sheet_paths(archive).items()
            if name not in drop
        }
    return make_workbook({**(first or {}), **sheets})


def economy_with_contents(release):
    return rebuild_workbook(
        make_test_xlsx(),
        first={
            "Contents": make_sheet(
                {
                    2: [
                        make_inline_cell(
                            "B2",
                            f"{release} Economic and fiscal outlook – detailed "
                            "forecast tables: economy",
                        )
                    ]
                }
            )
        },
    )


def test_main_refuses_release_flags_the_economy_tables_contradict(tmp_path):
    yoy, gap_dir = write_tree(tmp_path)
    before = {path: path.read_text() for path in [yoy, *gap_dir.iterdir()]}
    # The file is named March 2026 and the flags say March 2026, but the
    # workbook's contents sheet says November 2025.
    with pytest.raises(
        ValueError,
        match="economy tables are from November 2025, not March 2026",
    ):
        run_main(
            tmp_path,
            economy_with_contents("November 2025"),
            "--yaml-path",
            str(yoy),
        )
    assert {path: path.read_text() for path in before} == before


def test_main_takes_the_release_from_the_economy_contents_sheet(tmp_path):
    yoy, _ = write_tree(tmp_path)
    economy = tmp_path / "economy.xlsx"
    economy.write_bytes(economy_with_contents("March 2026"))
    receipts = tmp_path / "receipts.xlsx"
    receipts.write_bytes(make_receipts_xlsx())
    previous = tmp_path / "previous_receipts.xlsx"
    previous.write_bytes(make_previous_receipts_xlsx())
    assert (
        main(
            [
                "--file",
                str(economy),
                "--forecast-start-year",
                "2025",
                "--forecast-years",
                "2",
                "--receipts-file",
                str(receipts),
                "--previous-receipts-file",
                str(previous),
                "--yaml-path",
                str(yoy),
            ]
        )
        == 0
    )
    assert "OBR EFO March 2026" in yoy.read_text()


def test_release_is_read_from_a_url_encoded_name():
    url = "https://obr.uk/docs/March%202026%20Economic%20and%20fiscal%20outlook.xlsx"
    assert infer_release(url) == ("March", 2026)


@pytest.mark.parametrize(
    "flags", [["--skip-statutory-gaps"], [], ["--skip-statutory-gaps", "--dry-run"]]
)
def test_a_growth_only_run_does_not_need_september_cpi(tmp_path, flags):
    yoy, _ = write_tree(tmp_path)
    output = tmp_path / "out.yaml"
    # Receipts tables whose September CPI memo (sheet 3.19) is missing.
    no_cpi = rebuild_workbook(make_receipts_xlsx(), drop={"3.19"})
    with pytest.raises(ValueError, match="Could not find September CPI"):
        extract_september_cpi_from_receipts(no_cpi)
    assert (
        run_main(
            tmp_path,
            make_test_xlsx(),
            "--yaml-path",
            str(yoy),
            "--output",
            str(output),
            *flags,
            receipts=no_cpi,
        )
        == 0
    )
    assert yoy.read_text() == YOY_GROWTH_FIXTURE
    if "--dry-run" not in flags:
        assert _values(output.read_text(), RECEIPTS_PATHS["residential"])[2024] == 0.25


def test_a_forecast_year_a_series_lacks_is_named():
    # The fixture's series hold 2024-2026 and 2031, so a forecast reaching
    # 2027 has no entry to replace.
    values = {spec.key: {2025: 0.01, 2026: 0.02, 2027: 0.03} for spec in SERIES_SPECS}
    with pytest.raises(
        ValueError, match=f"{SERIES_SPECS[0].key} has no 2027-01-01 entry"
    ):
        render_yoy_growth_yaml(YOY_GROWTH_FIXTURE, values, "March", 2026, 2025, 3)


def test_gaps_only_refuses_the_previous_receipts_tables(tmp_path):
    yoy, _ = write_tree(tmp_path)
    with pytest.raises(ValueError, match="--gaps-only leaves yoy_growth.yaml alone"):
        run_main(tmp_path, make_test_xlsx(), "--yaml-path", str(yoy), "--gaps-only")


def test_main_writes_receipts_growth_to_the_output_path(tmp_path):
    yoy, _ = write_tree(tmp_path)
    output = tmp_path / "out.yaml"
    assert (
        run_main(
            tmp_path,
            make_test_xlsx(),
            "--yaml-path",
            str(yoy),
            "--output",
            str(output),
            "--skip-statutory-gaps",
        )
        == 0
    )
    assert yoy.read_text() == YOY_GROWTH_FIXTURE
    assert _values(output.read_text(), RECEIPTS_PATHS["residential"])[2024] == 0.25


# Gambling duty bases (#2738): each line's receipts over the rate the model
# charges, after HMRC's outturn.

GAMBLING_SPECS = tuple(spec for spec in RECEIPTS_SERIES_SPECS if spec.outturn)
# HMRC's 2024-25 and 2025-26 receipts, £bn (July 2026 Betting and Gaming
# tables, Table_1_BG_receipts rows 45 and 46).
HMRC_RECEIPTS = {
    "remote_gaming": (1.162539, 1.320966),
    "lottery": (0.931887, 0.980132),
    "general_betting": (0.713858, 0.684502),
    "machine_games": (0.609245, 0.641010),
    "gaming": (0.165397, 0.173902),
    "bingo": (0.025233, 0.026073),
    "pool_betting": (0.008125, 0.003970),
}
# The remote part of the General Betting Duty base, which pays 25% from
# 1 April 2027; the rest pays 15% throughout.
REMOTE_BETTING_SHARE = 2_163_978_657 / (2_471_124_767 + 2_163_978_657 + 123_949_909)
# Machine Games Duty's 2024-25 bands (£): HMRC's liabilities (Table_2_MGD
# row 20, £ thousand) over their rates, 5%, 20% and 25%.
MACHINE_GAMES_BANDS = {
    "lower": (6_921e3 / 0.05, 0.05),
    "standard": (604_748e3 / 0.20, 0.20),
    "higher": (596e3 / 0.25, 0.25),
}
# The Gambling Commission's 2024-25 gaming machine yield, £ million, in
# Category B and in Category C (Industry Statistics, April 2025 to March 2026
# release, sheet 4, K34 and L34).
HIGHER_STAKE_SHARE = 2_289.84969448829 / (2_289.84969448829 + 232.47489298159996)


def machine_games_rate(year, share=HIGHER_STAKE_SHARE):
    """Machine Games Duty's rate on its 2024-25 bands in the OBR's fiscal
    year ``year``: Budget 2026 moves ``share`` of the standard-rate band from
    20% to 25% on 1 April 2027, the first day of 2027-28."""
    total = sum(base for base, _ in MACHINE_GAMES_BANDS.values())
    charged = sum(base * rate for base, rate in MACHINE_GAMES_BANDS.values())
    if year >= 2027:
        charged += MACHINE_GAMES_BANDS["standard"][0] * share * 0.05
    return charged / total


def gambling_growth(**overrides):
    growth = compute_receipts_growth(
        make_receipts_xlsx(**overrides), b"not read", specs=GAMBLING_SPECS
    )
    return {path[-1]: series.values for path, series in growth.items()}


def ratio(new, old):
    return round(new / old - 1, 6)


def test_gambling_bases_take_out_the_rates_the_model_charges():
    """Synthetic March 2026 tables: growth from HMRC's 2024-25 receipts into
    the table's first year (2025-26), then the table's own years. Remote
    Gaming Duty's rise from 21% to 40% (1 April 2026) and the remote betting
    rise from 15% to 25% (1 April 2027) come out of the base, and so does the
    higher-stake machines' rise from 20% to 25% (1 April 2027); Bingo Duty's
    abolition (1 April 2026) holds its base flat."""
    growth = gambling_growth()
    hmrc = {key: values[0] for key, values in HMRC_RECEIPTS.items()}
    remote = 0.15 * (1 - REMOTE_BETTING_SHARE) + 0.25 * REMOTE_BETTING_SHARE
    expected = {
        "remote_gaming": {
            2025: ratio(1.4, hmrc["remote_gaming"]),
            # Receipts double (1.4 to 2.8), the base grows 5%.
            2026: ratio(2.8 / 0.40, 1.4 / 0.21),
            2027: ratio(2.94, 2.8),
        },
        "general_betting": {
            2025: ratio(0.7, hmrc["general_betting"]),
            2026: ratio(0.72, 0.7),
            2027: ratio(0.9 / remote, 0.72 / 0.15),
        },
        "bingo": {2025: ratio(0.03, hmrc["bingo"]), 2026: 0.0, 2027: 0.0},
        # Higher-stake machines pay 25% from 2027-28.
        "machine_games": {
            2025: ratio(0.65, hmrc["machine_games"]),
            2026: ratio(0.66, 0.65),
            2027: ratio(
                0.8 / machine_games_rate(2027), 0.66 / machine_games_rate(2026)
            ),
        },
    }
    for key in ("lottery", "gaming", "pool_betting"):
        levels = (hmrc[key], *GAMBLING_LEVELS[key])
        expected[key] = {2025 + i: ratio(levels[i + 1], levels[i]) for i in range(3)}
    assert growth.keys() == expected.keys()
    for key, values in expected.items():
        assert growth[key] == pytest.approx(values, abs=1.5e-6), key
    # Without the rate taken out, Remote Gaming Duty's 2026 growth would be
    # the receipts' 100%.
    assert growth["remote_gaming"][2026] == pytest.approx(0.05, abs=1e-6)


def test_real_october_2026_gambling_series():
    """The committed series, from Table 4.10 of the real October 2026 tables
    and HMRC's outturn, by hand."""
    growth = compute_receipts_growth(
        REAL_OCTOBER_2026_RECEIPTS, b"not read", specs=GAMBLING_SPECS
    )
    values = {path[-1]: series.values for path, series in growth.items()}
    # Remote Gaming Duty: 2026-27 at 40% over HMRC's 2025-26 at 21%.
    assert values["remote_gaming"][2026] == round(
        (2.7520296250837784 / 0.40) / (1.320966 / 0.21) - 1, 6
    )
    assert values["remote_gaming"][2026] == 0.093757
    # General Betting Duty: 2027-28 with its remote part at 25%.
    remote = 0.15 + 0.10 * REMOTE_BETTING_SHARE
    assert values["general_betting"][2027] == round(
        (0.87744453968275893 / remote) / (0.65560522982822456 / 0.15) - 1, 6
    )
    assert values["general_betting"][2027] == 0.027038
    # Machine Games Duty: 2027-28 with the higher-stake share at 25%.
    assert values["machine_games"][2027] == round(
        (0.82692873727074745 / machine_games_rate(2027))
        / (0.67707068705786499 / machine_games_rate(2026))
        - 1,
        6,
    )
    assert values["machine_games"][2027] == -0.002319
    assert values["bingo"] == dict.fromkeys(range(2026, 2032), 0.0) | {2025: 0.03329}
    for series in values.values():
        assert sorted(series) == list(range(2025, 2032))


def test_gambling_lines_read_no_previous_efo():
    # March 2025's tables have no betting and gaming breakdown; the gambling
    # lines take 2024-25 and 2025-26 from HMRC instead.
    real = compute_receipts_growth(REAL_RECEIPTS[2026], REAL_RECEIPTS[2025])
    alone = compute_receipts_growth(REAL_RECEIPTS[2026], b"", specs=GAMBLING_SPECS)
    assert {path: real[path].values for path in alone} == {
        path: series.values for path, series in alone.items()
    }
    assert all(series.previous_line is None for series in alone.values())


def test_gambling_outturn_must_reach_the_year_before_the_table():
    # A table from 2027-28 needs 2026-27 receipts, which HMRC has not
    # published in the July 2026 tables.
    with pytest.raises(ValueError, match="have no 2026-27, the year before Table"):
        compute_receipts_growth(
            make_receipts_xlsx(first_year=2026), b"", specs=GAMBLING_SPECS
        )


def test_bingo_holds_its_base_flat_after_the_forecast():
    rendered = render()
    start = rendered.index("    bingo:")
    block = rendered[start : rendered.index("    pool_betting:")]
    assert "# Beyond the OBR forecast: held flat, as the rate is zero" in block
    assert _values(rendered, GAMBLING_PATHS["bingo"])[2028] == 0.0
    assert max(_values(rendered, GAMBLING_PATHS["bingo"])) == 2028
    # Remote Gaming Duty follows average earnings, as the receipts lines do.
    remote_gaming = _values(rendered, GAMBLING_PATHS["remote_gaming"])
    assert {year: remote_gaming[year] for year in (2028, 2031)} == {
        2028: 0.0,
        2031: 0.02,
    }


def test_gambling_comments_and_references_name_hmrc_and_the_rates():
    rendered = render()
    block = rendered[
        rendered.index("    remote_gaming:") : rendered.index("    lottery:")
    ]
    # March 2026's table starts in 2025-26, so no year comes from HMRC alone.
    assert "# Outturn (2025" not in block
    assert (
        "# Forecast (2025-26 over 2024-25) from OBR EFO March 2026, receipts "
        'Table 3.10 "Remote gaming duty", over HMRC\'s receipts (July 2026 '
        "Betting and Gaming tables, Table_1_BG_receipts); base growth: receipts "
        "over the rate the model charges"
    ) in block
    references = _series(yaml.safe_load(rendered), GAMBLING_PATHS["remote_gaming"])[
        "metadata"
    ]["reference"]
    assert [reference["title"] for reference in references] == [
        "OBR EFO March 2026 (detailed forecast tables, receipts, Table 3.10)",
        "HMRC UK Betting and Gaming Statistics, July 2026 tables "
        "(Table_1_BG_receipts, 2024-25 and 2025-26 receipts)",
    ]


def test_the_machine_games_parameters_are_the_oracles():
    """The hand-written Machine Games Duty rates above are the model's: 5%,
    20% and 25%, with higher-stake machines at the higher rate from 1 April
    2027."""
    folder = Path(__file__).parents[1] / "parameters/gov/hmrc/gambling_duty"

    def values(name):
        data = yaml.safe_load((folder / f"machine_games/{name}.yaml").read_text())
        return {
            str(day): value["value"] if isinstance(value, dict) else value
            for day, value in data["values"].items()
        }

    assert values("rates/lower") == {"2013-02-01": 0.05}
    assert values("rates/standard") == {"2013-02-01": 0.2}
    assert values("rates/higher") == {"2015-03-01": 0.25}
    assert values("higher_stake_machines_at_higher_rate") == {
        "2013-02-01": False,
        "2027-04-01": True,
    }


def test_the_higher_stake_share_is_category_b_over_b_and_c():
    assert MACHINE_GAMES_HIGHER_STAKE_SHARE == HIGHER_STAKE_SHARE
    assert HIGHER_STAKE_SHARE == pytest.approx(0.907833, abs=1e-6)
    spec = machine_games_spec(HIGHER_STAKE_SHARE)
    assert spec in GAMBLING_SPECS
    standard = MACHINE_GAMES_BANDS["standard"][0]
    assert [part.weight for part in spec.rates] == pytest.approx(
        [
            MACHINE_GAMES_BANDS["lower"][0],
            standard * (1 - HIGHER_STAKE_SHARE),
            standard * HIGHER_STAKE_SHARE,
            MACHINE_GAMES_BANDS["higher"][0],
        ]
    )


def machine_games_levels(levels):
    """A synthetic March 2026 workbook whose Machine Games Duty line is
    ``levels`` from 2025-26 (the other lines are 1)."""
    return make_receipts_xlsx(
        gambling_levels={key: (1.0,) * len(levels) for key in GAMBLING_LABELS}
        | {"machine_games": tuple(levels)}
    )


def machine_games_growth(spec, levels):
    growth = compute_receipts_growth(machine_games_levels(levels), b"", specs=(spec,))
    return growth[spec.path].values


def test_a_rise_that_behaviour_offsets_gives_a_base_index_of_0_8():
    """£100 of higher-stake takings pay £20 at 20%. If the rise to 25% cuts
    them to £80, they pay the same £20 and receipts hold flat. The base index
    falls to 0.8, so the model's 25% on the projected £80 gives back £20."""
    spec = machine_games_spec(1.0)
    standard_only = replace(
        spec,
        rates=tuple(part for part in spec.rates if part.parameter.endswith("standard")),
        outturn=replace(spec.outturn, receipts_thousands=((2024, 20e3),)),
    )
    values = machine_games_growth(standard_only, (0.02, 0.02, 0.02))
    assert values == {2025: 0.0, 2026: 0.0, 2027: -0.2}
    index = (1 + values[2025]) * (1 + values[2026]) * (1 + values[2027])
    assert index == pytest.approx(0.8, abs=1e-12)
    assert 100 * index * 0.25 == pytest.approx(20, abs=1e-9)


SHARES = st.floats(min_value=0, max_value=1, allow_nan=False)


@settings(max_examples=60, deadline=None, derandomize=True)
@given(share=SHARES, levels=st.lists(LEVELS, min_size=5, max_size=5))
def test_machine_games_bases_reconcile_to_receipts_at_any_share(share, levels):
    """For any higher-stake share and any receipts path from 2025-26 to
    2029-30: each year's growth is the receipts' growth over the growth in
    the rate the model charges with that share at 25% from 2027-28. So a base
    that gives 2024-25's receipts gives every later year's at that rate, to
    within the rounding of the six-decimal growth."""
    values = machine_games_growth(machine_games_spec(share), levels)
    receipts = {2024: HMRC_RECEIPTS["machine_games"][0]}
    receipts |= dict(zip(range(2025, 2030), levels))
    rates = {year: machine_games_rate(year, share) for year in receipts}
    assert sorted(values) == list(range(2025, 2030))
    base = receipts[2024] / rates[2024]
    tolerance = 1.0
    for year in range(2025, 2030):
        exact = (receipts[year] / rates[year]) / (receipts[year - 1] / rates[year - 1])
        assert values[year] == pytest.approx(exact - 1, abs=5.1e-7)
        base *= 1 + values[year]
        tolerance *= 1 + 5.1e-7 / exact
        assert base * rates[year] == pytest.approx(
            receipts[year], rel=tolerance - 1 + 1e-12
        )


@settings(max_examples=40, deadline=None, derandomize=True)
@given(levels=st.lists(LEVELS, min_size=5, max_size=5))
def test_a_zero_share_grows_the_machine_games_base_with_receipts(levels):
    """With no higher-stake share the rate does not change, so the base grows
    with receipts: the plain rule of receipts over the rate, the series of
    the three bands alone."""
    zero = machine_games_spec(0.0)
    bands = replace(zero, rates=tuple(part for part in zero.rates if not part.switch))
    assert len(bands.rates) == 3
    values = machine_games_growth(zero, levels)
    assert values == machine_games_growth(bands, levels)
    receipts = {2024: HMRC_RECEIPTS["machine_games"][0]}
    receipts |= dict(zip(range(2025, 2030), levels))
    assert values == pytest.approx(
        {year: receipts[year] / receipts[year - 1] - 1 for year in range(2025, 2030)},
        abs=5.1e-7,
    )


GAMBLING_RATE_PARAMETERS = sorted(
    {path for spec in GAMBLING_SPECS for part in spec.rates for path in part.paths}
)
SWITCHES = {part.switch for spec in GAMBLING_SPECS for part in spec.rates} - {None}
RATE = st.floats(min_value=0.01, max_value=0.6, allow_nan=False)


@st.composite
def rate_schedules(draw):
    """Dated values for every gambling rate parameter: a first value, then
    perhaps a change on any day from 2024 to 2028, to zero or not. A switch
    takes true or false, read as 1 or 0."""
    schedules = {}
    for parameter in GAMBLING_RATE_PARAMETERS:
        value = st.booleans().map(float) if parameter in SWITCHES else RATE
        changed = st.booleans().map(float) if parameter in SWITCHES else RATE
        entries = [(date(2015, 1, 1), draw(value))]
        if draw(st.booleans()):
            day = draw(st.dates(date(2024, 1, 1), date(2028, 12, 31)))
            entries.append((day, draw(st.one_of(st.just(0.0), changed))))
        schedules[parameter] = tuple(entries)
    return schedules


def oracle_rate(spec, schedules, year):
    """The weighted mean of each part's daily rate over 1 April to 31 March.
    A switched part pays its switched rate on the days its switch is on."""
    days = [
        date.fromordinal(day)
        for day in range(date(year, 4, 1).toordinal(), date(year + 1, 4, 1).toordinal())
    ]

    def on(parameter, day):
        entries = schedules[parameter]
        return max((e for e in entries if e[0] <= day), default=entries[0])[1]

    total = sum(component.weight for component in spec.rates)
    mean = 0.0
    for component in spec.rates:
        daily = [
            on(component.switched, day)
            if component.switch and on(component.switch, day)
            else on(component.parameter, day)
            for day in days
        ]
        mean += component.weight * sum(daily) / len(daily)
    return mean / total


def oracle_growth(spec, receipts, schedules):
    """Each year's base growth to six decimals, and whether the index the
    model compounds from it, rounded to five decimals, reaches zero."""
    rates = {year: oracle_rate(spec, schedules, year) for year in receipts}
    growth, index, zero = {}, 1.0, False
    for year in sorted(receipts)[1:]:
        if rates[year] < 1e-12 or rates[year - 1] < 1e-12:
            growth[year] = 0.0
        else:
            exact = (receipts[year] / rates[year]) / (
                receipts[year - 1] / rates[year - 1]
            )
            growth[year] = round(exact - 1, 6)
        index = round(index * (1 + growth[year]), 5)
        zero = zero or index <= 0
    return growth, rates, zero


def gambling_receipts(key, levels):
    return {
        2024: HMRC_RECEIPTS[key][0],
        **dict(zip(range(2025, 2025 + len(levels)), levels)),
    }


@settings(max_examples=40, deadline=None, derandomize=True)
@given(
    levels=st.fixed_dictionaries(
        {key: st.tuples(LEVELS, LEVELS, LEVELS) for key in GAMBLING_LABELS}
    ),
    schedules=rate_schedules(),
    factor=st.floats(min_value=0.1, max_value=10, allow_nan=False),
)
def test_base_growth_is_receipts_growth_over_rate_growth(levels, schedules, factor):
    """For any positive receipts and dated rates: one plus each year's growth
    times the rate's growth is the receipts' growth (to the six decimals
    written); a year whose rate, or the year before's, is zero holds the base
    flat; and one factor on every rate, a rate reform the model applies
    itself, changes no growth. A series whose index would round to zero is
    refused instead."""
    module = import_obr_forecasts
    workbook = make_receipts_xlsx(gambling_levels=levels)
    scaled = {
        parameter: tuple(
            (day, value if parameter in SWITCHES else value * factor)
            for day, value in entries
        )
        for parameter, entries in schedules.items()
    }
    oracles = {
        spec.path: oracle_growth(
            spec, gambling_receipts(spec.path[-1], levels[spec.path[-1]]), schedules
        )
        for spec in GAMBLING_SPECS
    }
    with pytest.MonkeyPatch.context() as patch:
        if any(zero for _, _, zero in oracles.values()):
            event("refused")
            patch.setattr(module, "parameter_values", lambda p: schedules[p])
            with pytest.raises(ValueError, match="too small to grow from"):
                compute_receipts_growth(workbook, b"", specs=GAMBLING_SPECS)
            return
        event("written")
        patch.setattr(module, "parameter_values", lambda p: schedules[p])
        growth = compute_receipts_growth(workbook, b"", specs=GAMBLING_SPECS)
        patch.setattr(module, "parameter_values", lambda p: scaled[p])
        growth_scaled = compute_receipts_growth(workbook, b"", specs=GAMBLING_SPECS)
    for spec in GAMBLING_SPECS:
        values = growth[spec.path].values
        receipts = gambling_receipts(spec.path[-1], levels[spec.path[-1]])
        expected, rates, _ = oracles[spec.path]
        assert sorted(values) == [2025, 2026, 2027]
        for year, value in values.items():
            if rates[year] < 1e-12 or rates[year - 1] < 1e-12:
                assert value == 0.0
            else:
                exact = (receipts[year] / rates[year]) / (
                    receipts[year - 1] / rates[year - 1]
                )
                assert value == pytest.approx(exact - 1, abs=1e-6, rel=1e-9)
                assert 1 + value > 0
        assert growth_scaled[spec.path].values == pytest.approx(values, abs=1.5e-6)


def test_a_fall_that_rounds_the_index_to_zero_is_refused():
    """Receipts that fall from £1,000bn to £0.01bn as the rate rises from 1%
    to 60% shrink the base by a factor of six million. To six decimals that
    growth is -100%, which would hold the index at zero in every later year,
    so the importer refuses it."""
    spec = next(spec for spec in GAMBLING_SPECS if spec.path[-1] == "remote_gaming")
    workbook = make_receipts_xlsx(
        gambling_levels=GAMBLING_LEVELS | {"remote_gaming": (1000.0, 0.01, 0.01)}
    )
    schedule = ((date(2015, 1, 1), 0.01), (date(2026, 4, 1), 0.6))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(import_obr_forecasts, "parameter_values", lambda p: schedule)
        with pytest.raises(
            ValueError,
            match="2026-27 growth of -1.0 takes the index to 0.0 at five decimals",
        ):
            compute_receipts_growth(workbook, b"", specs=(spec,))


POSITIVE = st.one_of(LEVELS, st.floats(min_value=1e-9, max_value=1e-2, allow_nan=False))


@settings(max_examples=60, deadline=None, derandomize=True)
@given(
    levels=st.fixed_dictionaries(
        {key: st.tuples(POSITIVE, POSITIVE, POSITIVE) for key in GAMBLING_LABELS}
    ),
    schedules=rate_schedules(),
)
def test_a_written_series_keeps_every_index_positive(levels, schedules):
    """For any positive receipts, however small, and any dated rates: the
    importer either refuses, when the written growth would round the model's
    index to zero, or writes series whose index the model compounds to five
    decimals stays above zero in every year."""
    workbook = make_receipts_xlsx(gambling_levels=levels)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(import_obr_forecasts, "parameter_values", lambda p: schedules[p])
        try:
            growth = compute_receipts_growth(workbook, b"", specs=GAMBLING_SPECS)
        except ValueError as error:
            event("refused")
            assert "too small to grow from" in str(error)
            assert any(
                oracle_growth(
                    spec,
                    gambling_receipts(spec.path[-1], levels[spec.path[-1]]),
                    schedules,
                )[2]
                for spec in GAMBLING_SPECS
            )
            return
    event("written")
    for series in growth.values():
        index = 1.0
        for year in sorted(series.values):
            index = round(index * (1 + series.values[year]), 5)
            assert index > 0
