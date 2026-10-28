"""Population growth and the per-capita series come from one OBR vintage.

ons.population, 2023-2073: the population growth row of the OBR's
"Long-term economic determinants - March 2026 Economic and fiscal outlook"
(28 May 2026), per cent, fiscal year t-(t+1) stored at t-01-01. To 2030-31 it
is the OBR's March 2026 forecast; after that, the principal projection of the
ONS 2024-based national population projections.

ons.population, 2021-2022: the release starts at 2023-24, so the same OBR
series is read from the March 2026 EFO detailed forecast tables (economy):
population at Q2 = Table 1.1 real GDP / Table 1.5 real GDP per person (total
population, index 2008Q1=100). That ratio reproduces the release's 2023-24 to
2025-26 values to 1e-9 per cent.

per_capita.*: (1 + aggregate growth) / (1 + ons.population) - 1, rounded to 4
decimals, with calendar-year aggregates from the October 2026 EFO tables. The
long-term determinants for the October 2026 EFO are not yet published, so
population stays on the March 2026 vintage until they are.
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

# March 2026 EFO economy tables, Q2 of each year.
# Table 1.1 real GDP, GBP billion chain-linked volumes.
REAL_GDP_Q2 = {
    2020: 522.356,
    2021: 655.443,
    2022: 686.335,
    2023: 689.491,
    2024: 695.28,
    2025: 704.973,
}
# Table 1.5 real GDP per person (total population), index 2008Q1=100.
REAL_GDP_PER_PERSON_Q2 = {
    2020: 82.30813961942992,
    2021: 102.91179537890864,
    2022: 106.71381138411466,
    2023: 105.81216977918598,
    2024: 105.53778853635153,
    2025: 106.69186884652444,
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


def q2_population_growth_percent(year):
    population = {
        y: REAL_GDP_Q2[y] / REAL_GDP_PER_PERSON_Q2[y] for y in (year - 1, year)
    }
    return (population[year] / population[year - 1] - 1) * 100


@pytest.mark.parametrize("year", sorted(LTED_MARCH_2026_POPULATION_GROWTH))
def test_population_is_the_march_2026_long_term_determinants_row(year):
    expected = round(LTED_MARCH_2026_POPULATION_GROWTH[year] / 100, 4)
    assert POPULATION(f"{year}-01-01") == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("year", [2023, 2024, 2025])
def test_efo_tables_reproduce_the_release(year):
    assert q2_population_growth_percent(year) == pytest.approx(
        LTED_MARCH_2026_POPULATION_GROWTH[year], abs=1e-9
    )


@pytest.mark.parametrize("year, expected", [(2021, 0.0036), (2022, 0.0098)])
def test_population_before_the_release_comes_from_the_efo_tables(year, expected):
    # 2021: 0.3566% and 2022: 0.9824%, rounded to 4 decimals.
    assert round(q2_population_growth_percent(year) / 100, 4) == expected
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
