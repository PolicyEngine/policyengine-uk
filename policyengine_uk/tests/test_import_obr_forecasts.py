import os
from datetime import date
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.utils import import_obr_forecasts

from policyengine_uk.utils.import_obr_forecasts import (
    RECEIPTS_SERIES_SPECS,
    SERIES_SPECS,
    STATUTORY_GAP_SPECS,
    _sheet_paths,
    ForecastGap,
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


def make_receipts_xlsx(
    release: str | None = "March 2026",
    first_year: int = 2024,
    levels: dict[str, tuple] | None = None,
    cash_table: str = "3.8",
    northern_ireland_label: str = "Northern Ireland business rates",
    outturn_years: int = 1,
    sdlt_rows: list[tuple[str, tuple]] | None = None,
) -> bytes:
    levels = levels or RECEIPTS_LEVELS
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
                6: [make_inline_cell("B6", "3.2 Other taxes")],
            }
        )
    sheets["3.2"] = receipts_table(
        "3.2 Other taxes",
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
    sheets["3.7"] = receipts_table(
        "3.7 Property transactions taxes: Receipts by sector",
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
    sheets["3.5"] = receipts_table(
        "3.5 Current receipts (on an accrued basis)",
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
    sheets["3.18"] = sheet_318
    sheets["3.19"] = sheet_319
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


# Receipts growth series: stamp_duty_land_tax and business_rates under obr.

RECEIPTS_PATHS = {spec.path[-1]: spec.path for spec in RECEIPTS_SERIES_SPECS}


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
        for spec in RECEIPTS_SERIES_SPECS
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
    assert {path[-1]: series.values for path, series in growth.items()} == {
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
        for path in RECEIPTS_PATHS.values():
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
        ".".join(path) for path in RECEIPTS_PATHS.values()
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


# Published OBR receipts levels as the workbooks hold them (£bn): the March
# 2026 EFO from 2024-25 and the March 2025 EFO from 2023-24.
MARCH_2026_RECEIPTS = {
    "residential": ("10.379999999999999", "11.731471524432562", "13.428906667032589", "14.984943814530874", "16.673948133476184", "17.964513468126285", "19.057301113969185"),
    "non_residential": ("3.5049999999999999", "3.6750451743530199", "4.72127759316189", "5.3288288104799904", "5.9009139798817092", "6.5330695355310402", "7.1046581772762902"),
    "great_britain": ("32.376814327646052", "34.051963932489258", "37.413586572144581", "38.240930947824609", "39.111850954748434", "42.419067764546902", "42.463193622519263"),
    "northern_ireland": ("0.38233350730688931", "0.39471664406441903", "0.40263364127921164", "0.41045270712298504", "0.41810894612429189", "0.42590403232705243", "0.43449009714292341"),
}  # fmt: skip
MARCH_2025_RECEIPTS = {
    "residential": ("8.57", "10.067621905140079", "11.260655778417849", "13.448356441943533", "15.629462727222798", "17.837320625934193", "19.309303893346414"),
    "non_residential": ("3.0449999999999999", "3.51897590165244", "2.8597545561212101", "3.7329253327014698", "4.2294622915006306", "4.6980571035732099", "5.2115072362568595"),
    "great_britain": ("29.599814327646055", "32.080747417794186", "34.009749097370083", "37.622908483210999", "37.878733699384433", "38.522006059307493", "39.56809170547703"),
    "northern_ireland": ("0.37029404557706441", "0.38436854999535813", "0.39453673994468591", "0.40107161940999719", "0.40924102844267779", "0.41720986951771938", "0.42505803014305893"),
}  # fmt: skip


def test_march_2026_tables_reproduce_the_committed_series():
    """yoy_growth.yaml holds exactly what the importer writes from the March
    2026 receipts tables (Tables 3.7, 3.8 and 3.2) and the March 2025 ones
    (3.7, 3.9 and 3.2): rerunning it on the committed file changes nothing."""
    committed = get_yoy_growth_path().read_text()
    rendered = render(
        committed,
        current=make_receipts_xlsx(levels=MARCH_2026_RECEIPTS),
        previous=make_previous_receipts_xlsx(levels=MARCH_2025_RECEIPTS),
    )
    assert rendered == committed


REAL_RECEIPTS_DIR = Path(__file__).parent / "fixtures" / "obr_receipts"
REAL_RECEIPTS = {
    year: (REAL_RECEIPTS_DIR / f"obr_efo_march_{year}_receipts.xlsx").read_bytes()
    for year in (2025, 2026)
}
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
        first_column = "D" if table in ("3.8", "3.9") else "C"
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
        committed.decode(), current=REAL_RECEIPTS[2026], previous=REAL_RECEIPTS[2025]
    )
    assert rendered.encode() == committed


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
        yoy, gap_dir = write_tree(tmp_path)
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
            current=mutate_real_receipts(REAL_RECEIPTS[2026], "3.8", unit),
            previous=mutate_real_receipts(REAL_RECEIPTS[2025], "3.9", unit),
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
    for path in RECEIPTS_PATHS.values():
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
