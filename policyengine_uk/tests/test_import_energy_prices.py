"""The energy price importer reproduces the committed inputs from real sources.

The fixtures are the real ONS, OBR and DESNZ files cut down to what the
importer reads (see ``fixtures/energy_prices/README.md``). Tests that change
them change copies in memory.
"""

import csv
import io
from pathlib import Path
from zipfile import ZipFile

import pytest

from policyengine_uk.utils import import_energy_prices as importer

FIXTURES = Path(__file__).parent / "fixtures" / "energy_prices"
MM23 = FIXTURES / "mm23_energy_columns.csv"
OBR = FIXTURES / "efo_october_2026_economy_table_1_19.xlsx"
ELECTRICITY = FIXTURES / "ET_5.2_SEP_26_quarter.xlsx"
GAS = FIXTURES / "ET_4.1_SEP_26_quarter_gwh.xlsx"
OUTPUTS = ("ons.yaml", "obr.yaml", "consumption_shares.yaml")


def render(mm23=None, obr=None):
    return importer.render_all(
        MM23.read_text(encoding="utf-8-sig") if mm23 is None else mm23,
        OBR.read_bytes() if obr is None else obr,
        OBR.name,
        ELECTRICITY.read_bytes(),
        GAS.read_bytes(),
    )


def mm23_rows():
    return list(csv.reader(io.StringIO(MM23.read_text(encoding="utf-8-sig"))))


def to_csv(rows):
    buffer = io.StringIO()
    csv.writer(buffer, quoting=csv.QUOTE_ALL, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


def test_real_sources_reproduce_the_committed_yaml_byte_for_byte():
    rendered = render()
    assert sorted(rendered) == sorted(OUTPUTS)
    for name, text in rendered.items():
        assert text.encode() == (importer.PARAMETER_DIR / name).read_bytes(), name


def test_main_writes_every_file(tmp_path):
    importer.main(
        [
            "--mm23",
            str(MM23),
            "--obr-economy",
            str(OBR),
            "--electricity-trends",
            str(ELECTRICITY),
            "--gas-trends",
            str(GAS),
            "--output-dir",
            str(tmp_path),
        ]
    )
    for name in OUTPUTS:
        assert (tmp_path / name).read_bytes() == (
            importer.PARAMETER_DIR / name
        ).read_bytes()
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(OUTPUTS)


def test_the_forecast_starts_after_the_last_full_ons_quarter():
    # Without September 2026, ONS has the third quarter only in part, so the
    # OBR's rate for it (3.7143% in Table 1.19) is the first one kept.
    rows = [row for row in mm23_rows() if row[0] != "2026 SEP"]
    obr = render(mm23=to_csv(rows))["obr.yaml"]
    values = obr.split("  values:\n")[1].splitlines()
    assert values[0] == "    2026-07-01: 0.037143"
    assert values[1] == "    2026-10-01: 0.045313"
    assert "first quarter ONS has not published in full (2026Q3)" in obr


def test_a_missing_month_is_an_error():
    rows = mm23_rows()
    column = rows[1].index("D7DU")
    for row in rows:
        if row[0] == "2020 MAY":
            row[column] = ""
    with pytest.raises(ValueError, match="D7DU has gaps"):
        render(mm23=to_csv(rows))


def test_a_missing_series_is_an_error():
    rows = [row[:-1] for row in mm23_rows()]
    with pytest.raises(ValueError, match="A9F4"):
        render(mm23=to_csv(rows))


def test_series_from_different_releases_are_an_error():
    rows = mm23_rows()
    rows[4][1] = "18-11-2026"
    with pytest.raises(ValueError, match="different releases"):
        render(mm23=to_csv(rows))


def replace_in_workbook(data, old, new):
    source = ZipFile(io.BytesIO(data))
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as target:
        for item in source.infolist():
            content = source.read(item.filename)
            if item.filename == "xl/sharedStrings.xml":
                assert old.encode() in content
                content = content.replace(old.encode(), new.encode())
            target.writestr(item, content)
    return buffer.getvalue()


def test_a_table_without_a_utilities_column_is_an_error():
    obr = replace_in_workbook(OBR.read_bytes(), ">Utilities<", ">Water<")
    with pytest.raises(ValueError, match="one Utilities column"):
        render(obr=obr)


def test_a_different_table_is_an_error():
    obr = replace_in_workbook(OBR.read_bytes(), "CPI category inflation", "Other")
    with pytest.raises(ValueError, match="not the CPI category inflation table"):
        render(obr=obr)


def test_seasonal_shares_average_each_complete_year_from_2015():
    consumption = {(2014, q): 1.0 for q in range(1, 5)}
    consumption.update({(2015, q): v for q, v in zip(range(1, 5), (4, 3, 2, 1))})
    consumption.update({(2016, q): v for q, v in zip(range(1, 5), (1, 1, 1, 1))})
    consumption[(2017, 1)] = 9.0
    shares, last = importer.seasonal_shares(consumption)
    assert last == 2016
    assert shares == [0.325, 0.275, 0.225, 0.175]


def test_seasonal_shares_need_complete_years_from_2015():
    consumption = {(2015, q): 1.0 for q in range(2, 5)}
    with pytest.raises(ValueError, match="complete years from 2015"):
        importer.seasonal_shares(consumption)
