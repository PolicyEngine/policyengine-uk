from io import BytesIO
from zipfile import ZipFile

from policyengine_uk.utils.import_obr_forecasts import (
    STATUTORY_GAP_SPECS,
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


def make_test_xlsx() -> bytes:
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
            99: [
                make_inline_cell("B99", "2026Q2"),
                make_number_cell("Q99", 3.67),
            ],
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


def make_receipts_xlsx() -> bytes:
    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="3.18" sheetId="1" r:id="rId1"/>
    <sheet name="3.19" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>
"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
</Relationships>
"""
    sheet_318 = make_sheet({2: [make_inline_cell("B2", "Other table")]})
    sheet_319 = make_sheet(
        {
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
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_318)
        archive.writestr("xl/worksheets/sheet2.xml", sheet_319)
    return buffer.getvalue()


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
