"""Population growth and the per-capita series come from one OBR vintage.

ons.population, 2021-2031: the OBR's October 2026 population, read from the
October 2026 EFO detailed forecast tables (economy): population at Q2 = Table
1.1 real GDP / Table 1.5 real GDP per person (total population, index
2008Q1=100), fiscal year t-(t+1) stored at t-01-01. The long-term economic
determinants for the October 2026 EFO are not yet published. For the March
2026 EFO the same ratio on its own tables reproduces the determinants'
2023-24 to 2030-31 values to 1e-9 per cent, so the tables give the OBR's
population forecast.

ons.population, 2032-2073: the population growth row of the OBR's
"Long-term economic determinants - March 2026 Economic and fiscal outlook"
(28 May 2026), which from 2031-32 is the principal projection of the ONS
2024-based national population projections.

per_capita.*: (1 + aggregate growth) / (1 + ons.population) - 1, rounded to 4
decimals, with calendar-year aggregates from the October 2026 EFO tables.
"""

import pytest

from policyengine_uk.system import system

YOY = system.parameters.gov.economic_assumptions.yoy_growth
POPULATION = YOY.ons.population

# OBR long-term economic determinants, March 2026 EFO: population growth, %.
LTED_MARCH_2026_POPULATION_GROWTH = {
    2023: 1.3158672896090877,
    2024: 1.1017715903452796,
    2025: 0.29733981899798323,
    2026: 0.3513313012721113,
    2027: 0.28846436048186774,
    2028: 0.3221199806863382,
    2029: 0.33740683300655405,
    2030: 0.3633675140245316,
    2031: 0.2388497010895163,
    2032: 0.22370075378450593,
    2033: 0.2088704995126811,
    2034: 0.19480847931587775,
    2035: 0.18209972234002336,
    2036: 0.17105370632082284,
    2037: 0.16149757764156725,
    2038: 0.15337082743571706,
    2039: 0.14645525205250198,
    2040: 0.14059256520155827,
    2041: 0.13544502807449899,
    2042: 0.13065266604816994,
    2043: 0.1258303566855412,
    2044: 0.12057608878321968,
    2045: 0.11394765412899854,
    2046: 0.10597542494543699,
    2047: 0.09714837762127004,
    2048: 0.08728256097529918,
    2049: 0.07626452247553317,
    2050: 0.06324271154818373,
    2051: 0.04847236420357781,
    2052: 0.03311728764627819,
    2053: 0.01733576022024952,
    2054: 0.0014408344165772746,
    2055: -0.014031732617858506,
    2056: -0.028358364675085124,
    2057: -0.041173708067321346,
    2058: -0.05246738930690942,
    2059: -0.062196733283259586,
    2060: -0.07017357235220567,
    2061: -0.07644675557505476,
    2062: -0.08105844946758589,
    2063: -0.08446815098064331,
    2064: -0.08701048822423729,
    2065: -0.08868551161084204,
    2066: -0.0897568416164729,
    2067: -0.09044608293788947,
    2068: -0.09115102662563546,
    2069: -0.09215432481369801,
    2070: -0.09377616180261672,
    2071: -0.09615695591076445,
    2072: -0.09939184042673244,
    2073: -0.10361433924080954,
}

# EFO economy tables, Q2 of each year: Table 1.1 real GDP (GBP billion
# chain-linked volumes) and Table 1.5 real GDP per person (total population,
# index 2008Q1=100).
MARCH_2026_Q2 = {
    "real_gdp": {
        2020: 522.356,
        2021: 655.443,
        2022: 686.335,
        2023: 689.491,
        2024: 695.28,
        2025: 704.973,
        2026: 711.4752108974202,
        2027: 722.8696711355229,
        2028: 734.3003452895008,
        2029: 745.6888920481834,
        2030: 756.9312657071862,
    },
    "per_person": {
        2020: 82.30813961942992,
        2021: 102.91179537890864,
        2022: 106.71381138411466,
        2023: 105.81216977918598,
        2024: 105.53778853635153,
        2025: 106.69186884652444,
        2026: 107.29895022122213,
        2027: 108.70379905059379,
        2028: 110.06817103615971,
        2029: 111.39939151779004,
        2030: 112.66949934985858,
    },
}
OCTOBER_2026_Q2 = {
    "real_gdp": {
        2020: 522.356,
        2021: 655.443,
        2022: 686.335,
        2023: 689.491,
        2024: 694.91,
        2025: 704.274,
        2026: 712.545,
        2027: 719.317942019668,
        2028: 730.6639315269857,
        2029: 743.9492331304032,
        2030: 756.6079210550221,
        2031: 768.8776481950802,
    },
    "per_person": {
        2020: 82.30813961942992,
        2021: 102.91179537890864,
        2022: 106.64443479278931,
        2023: 105.71652105745173,
        2024: 105.51970228805975,
        2025: 106.58608094213133,
        2026: 107.61945209228196,
        2027: 108.49781352227016,
        2028: 110.01755336744607,
        2029: 111.78317881384578,
        2030: 113.40385957086,
        2031: 114.96729664409621,
    },
}

# October 2026 EFO calendar-year totals, GBP billion.
# Table 1.4 nominal GDP (annual growth equals Table A.1 nominal GDP growth).
NOMINAL_GDP = {
    2020: 2124.72,
    2021: 2322.652,
    2022: 2580.949,
    2023: 2752.164,
    2024: 2890.254,
    2025: 3033.866,
    2026: 3161.458961,
    2027: 3263.816753,
    2028: 3381.78475,
    2029: 3510.878469,
    2030: 3640.284132,
    2031: 3770.105082,
}
# Table 1.12 mixed income.
MIXED_INCOME = {
    2020: 152.109,
    2021: 162.369,
    2022: 168.687,
    2023: 169.885,
    2024: 176.333,
    2025: 177.725,
    2026: 183.374482,
    2027: 189.543244,
    2028: 196.611717,
    2029: 204.513402,
    2030: 213.30725,
    2031: 222.381054,
}


def q2_population_growth_percent(tables, year):
    population = {
        y: tables["real_gdp"][y] / tables["per_person"][y] for y in (year - 1, year)
    }
    return (population[year] / population[year - 1] - 1) * 100


@pytest.mark.parametrize("year", range(2023, 2031))
def test_efo_tables_reproduce_the_long_term_determinants(year):
    """On the March 2026 EFO, the tables give the determinants' forecast."""
    assert q2_population_growth_percent(MARCH_2026_Q2, year) == pytest.approx(
        LTED_MARCH_2026_POPULATION_GROWTH[year], abs=1e-9
    )


@pytest.mark.parametrize("year", range(2021, 2032))
def test_population_to_2031_is_the_october_2026_efo_tables(year):
    expected = round(q2_population_growth_percent(OCTOBER_2026_Q2, year) / 100, 4)
    assert POPULATION(f"{year}-01-01") == pytest.approx(expected, abs=1e-12)


def test_october_population_grows_more_slowly_than_march():
    # 2026-27 to 2030-31: 0.13% to 0.25% a year, against 0.29% to 0.36% in
    # the March 2026 forecast, about 0.7% lower by 2030-31.
    level = 1.0
    for year in range(2026, 2031):
        level *= (1 + POPULATION(f"{year}-01-01")) / (
            1 + LTED_MARCH_2026_POPULATION_GROWTH[year] / 100
        )
    assert level == pytest.approx(1 - 0.0069, abs=0.0005)


@pytest.mark.parametrize("year", range(2032, 2074))
def test_population_after_2031_is_the_march_2026_determinants_row(year):
    expected = round(LTED_MARCH_2026_POPULATION_GROWTH[year] / 100, 4)
    assert POPULATION(f"{year}-01-01") == pytest.approx(expected, abs=1e-12)


def _per_capita(aggregate_growth, year):
    return round((1 + aggregate_growth) / (1 + POPULATION(f"{year}-01-01")) - 1, 4)


@pytest.mark.parametrize("year", range(2021, 2032))
def test_per_capita_gdp_divides_nominal_gdp_by_population(year):
    growth = NOMINAL_GDP[year] / NOMINAL_GDP[year - 1] - 1
    assert YOY.obr.per_capita.gdp(f"{year}-01-01") == pytest.approx(
        _per_capita(growth, year), abs=1e-12
    )


@pytest.mark.parametrize("year", range(2021, 2032))
def test_per_capita_mixed_income_divides_mixed_income_by_population(year):
    growth = MIXED_INCOME[year] / MIXED_INCOME[year - 1] - 1
    assert YOY.obr.per_capita.mixed_income(f"{year}-01-01") == pytest.approx(
        _per_capita(growth, year), abs=1e-12
    )


@pytest.mark.parametrize("year", range(2021, 2032))
def test_per_capita_non_labour_income_divides_by_population(year):
    growth = YOY.obr.non_labour_income(f"{year}-01-01")
    assert YOY.obr.per_capita.non_labour_income(f"{year}-01-01") == pytest.approx(
        _per_capita(growth, year), abs=1e-12
    )
