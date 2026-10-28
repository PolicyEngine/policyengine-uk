from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.capital_gains_projection import (
    CGT_DATASET_INPUTS,
    CGT_INDEX_PATH,
)
from policyengine_uk.data.savings_income_projection import (
    DEFAULT_SAVINGS_INCOME_PROJECTION,
    OBR_SAVINGS_INCOME_2022_2025,
    SAVINGS_INCOME_SERIES_YEARS,
    uniform_savings_income_projection,
    validate_savings_income_projection,
)
from policyengine_uk.data.isa_income import (
    ISA_INTEREST,
    SAVINGS_INTEREST,
    effective_tax_free,
    gross_interest,
    legacy_projection_source,
    ordinary_interest,
)

import hashlib

import yaml
from policyengine_core.parameters import ParameterNode
from policyengine_core.simulations.simulation import _uprating_index_value
from pathlib import Path
import numpy as np
import pandas as pd
import logging

from policyengine_uk.utils.stochastic import splitmix64_uniform

# Approximate take-up rate for assigning loans to tertiary-educated NONE people.
# This represents P(has loan AND earning above threshold | tertiary educated).
# Derived from SLC forecasts (~4M Plan 2 above threshold) vs UK graduate
# population (~8-10M in relevant age bands), giving roughly 40-50%.
# We use a conservative 0.4 as many graduates have paid off loans or earn
# below threshold.
_GRADUATE_LOAN_TAKE_UP = 0.4

_ENGLAND_REGIONS = {
    "NORTH_EAST",
    "NORTH_WEST",
    "YORKSHIRE",
    "EAST_MIDLANDS",
    "WEST_MIDLANDS",
    "EAST_OF_ENGLAND",
    "LONDON",
    "SOUTH_EAST",
    "SOUTH_WEST",
}

_PLAN1_WRITEOFF_YEARS = 29
# Plan 1 loans first paid before 1 September 2006 (the 2005 and earlier
# intakes) are written off at 65 instead (GOV.UK, "When your student loan
# gets written off or cancelled").
_PLAN1_LAST_AGE_65_WRITEOFF_UNI_START = 2005
_PLAN1_WRITEOFF_AGE = 65

# The first university intakes of income-contingent (Plan 1), Plan 2 and
# Plan 5 loans. The oldest holder of a plan in the year the data describe
# started university in its first intake, at 18.
_PLAN1_FIRST_UNI_START = 1998
_PLAN2_FIRST_UNI_START = 2012
_PLAN5_FIRST_UNI_START = 2023

# Salt for the student loan take-up draws, keyed on person_id. Other salts of
# splitmix64_uniform are used by variable formulas.
_STUDENT_LOAN_DRAW_SALT = 3

# The council tax growth series (a child of
# gov.economic_assumptions.yoy_growth.obr.council_tax) for each Region label.
# Northern Ireland has no council tax (the Local Government Finance Act 1992
# does not extend there; it levies domestic rates, carried in domestic_rates),
# OBR forecasts council tax for England, Scotland and Wales only, and the FRS
# gives Northern Ireland households none. So it has no series, and any council
# tax a dataset does give them is held flat. An unknown region takes England's
# series, the nearest to a Great Britain one: England raises 89% of the council
# tax OBR forecasts for 2025-26.
_COUNCIL_TAX_GROWTH_SERIES = {
    **dict.fromkeys(_ENGLAND_REGIONS, "england"),
    "WALES": "wales",
    "SCOTLAND": "scotland",
    "NORTHERN_IRELAND": None,
    "UNKNOWN": "england",
}

# The growth series (under gov.economic_assumptions.yoy_growth) of each Region
# label's water and sewerage charges (#2501). Ofwat's series is the average
# household bill in England and Wales. Scottish Water's charges follow limits
# set by the Water Industry Commission for Scotland. Northern Ireland has no
# domestic water charges, so any a dataset gives its households are held flat.
# Past PROJECTION_END_YEAR, policyengine-core grows the column by the index
# its variable declares (Ofwat's) in every country.
# An unknown region takes the England and Wales series, which covers most
# households in Great Britain.
WATER_BILLS_GROWTH = "gov.economic_assumptions.yoy_growth"
_WATER_GROWTH_SERIES = {
    **dict.fromkeys(_ENGLAND_REGIONS, "ofwat.water_bills"),
    "WALES": "ofwat.water_bills",
    "SCOTLAND": "scottish_water.water_bills",
    "NORTHERN_IRELAND": None,
    "UNKNOWN": "ofwat.water_bills",
}
# Inputs uprated by country in this module rather than through
# uprating_indices.yaml, so the index their variable declares must not grow
# them a second time after LEGACY_PROJECTION_END_YEAR.
COUNTRY_UPRATED_INPUTS = frozenset({"water_and_sewerage_charges"})

# Savings income (savings interest, ISA interest and other investment income)
# grows in dataset projection by the path the dataset declares it was
# calibrated to (savings_income_projection.py). Under the
# obr_savings_income_2022_2025 rule that is the OBR's savings income forecast
# per person from 2022-23 to 2025-26, and GDP per head in other years, like
# dividends and the other capital incomes. The OBR's series rises 35.0% in
# 2024-25 and 0.6% in 2025-26, where GDP per head rises 3.9% and 4.7%. It
# starts in 2022-23, so earlier years keep GDP per head rather than the
# parameter's backdated first value. A dataset that declares no rule grows
# savings income by GDP per head in every year, as before.
SAVINGS_INCOME_GROWTH = (
    "gov.economic_assumptions.yoy_growth.obr.per_capita.savings_income"
)
GDP_PER_HEAD_GROWTH = "gov.economic_assumptions.yoy_growth.obr.per_capita.gdp"
SAVINGS_INCOME_GROWTH_FIRST_YEAR, SAVINGS_INCOME_GROWTH_LAST_YEAR = (
    SAVINGS_INCOME_SERIES_YEARS[OBR_SAVINGS_INCOME_2022_2025]
)


def growth_rate(
    parameters: ParameterNode,
    index_name: str,
    year,
    savings_income_projection: str = DEFAULT_SAVINGS_INCOME_PROJECTION,
) -> float:
    """Growth into ``year`` by the uprating_indices.yaml series ``index_name``.

    The savings income series applies only in the years the dataset's
    ``savings_income_projection`` rule gives it; GDP per head serves the
    other years, and every year under the default rule.
    """
    if index_name == SAVINGS_INCOME_GROWTH:
        years = SAVINGS_INCOME_SERIES_YEARS[
            validate_savings_income_projection(savings_income_projection)
        ]
        if years is None or not years[0] <= int(str(year)[:4]) <= years[1]:
            index_name = GDP_PER_HEAD_GROWTH
    return parameters.get_child(index_name)(year)


# The last year a single-year dataset is projected to: 2032, fiscal year
# 2032-33. An OBR forecast runs five years past the fiscal year it is made in,
# so one made in 2026-27 ends in 2031-32 (year 2031). yoy_growth.yaml holds the
# March 2026 forecast, which ends in 2030-31. Move this on as forecasts move.
#
# Every year up to here is a dataset year, grown from the year before by
# apply_single_year_uprating. A growth series with no value for a year grows
# at its latest rate, so a series that the March 2026 forecast ends in 2030
# holds its 2030-31 rate in 2031-32 and 2032-33.
#
# Past this year policyengine-core serves each stored input from the last
# projected year. An input whose variable has a formula is calculated by it
# instead (pension_credit_reported_capital reads benunit_reported_capital,
# which the Enhanced FRS does not store, so it falls to -1); one whose
# variable has an `uprating` attribute is scaled by that index; any other,
# rent and council tax among them, is held at its last projected value.
# A finite CGT scenario can shorten the whole dataset horizon; it never
# extends beyond the evidence declared by that scenario.
PROJECTION_END_YEAR = 2032

# Before this horizon was extended, Core uprated unmapped inputs from 2030.
# Preserve that behavior in the newly materialized years without changing
# projections for earlier years. Correcting historical mapping omissions is
# a separate change. Energy has its own declaration-aware projection below,
# so it must not also grow through the generic variable-index fallback.
LEGACY_PROJECTION_END_YEAR = 2030
DECLARED_ENERGY_INPUTS = frozenset(
    {
        "domestic_energy_consumption",
        "electricity_consumption",
        "gas_consumption",
    }
)
DATASET_UPRATING_EXCLUSIONS = DECLARED_ENERGY_INPUTS
# Both separated benefits must be explicit before BSP can be held nominally flat.
BEREAVEMENT_SPLIT_INPUTS = frozenset(
    {"war_widows_pension_reported", "widowed_parents_allowance_reported"}
)
# Inputs that describe only the year they are stored for, so are not carried
# into projected years. Unused annual allowance comes from the three tax years
# before this one (Finance Act 2004 s. 228A), a window that moves each year; a
# projected year uses the variable's own estimate instead (#2523).
YEAR_SPECIFIC_INPUTS = frozenset({"unused_pension_annual_allowance"})


def _unmapped_uprating_indices(uprating):
    from policyengine_uk.system import system

    mapped = {variable for variables in uprating.values() for variable in variables}
    return {
        name: variable.uprating
        for name, variable in system.variables.items()
        if variable.uprating is not None
        and name not in mapped
        and name not in DATASET_UPRATING_EXCLUSIONS
        and name not in COUNTRY_UPRATED_INPUTS
    }


COUNCIL_TAX_GROWTH = "gov.economic_assumptions.yoy_growth.obr.council_tax"
SOCIAL_RENT_GROWTH = "gov.economic_assumptions.yoy_growth.obr.social_rent"
PRIVATE_RENT_GROWTH = "gov.economic_assumptions.yoy_growth.ons.private_rental_prices"
RESIDENTIAL_PROPERTY_INDEX = "gov.economic_assumptions.indices.obr.house_prices"
ENERGY_PRICE_INDEX = "gov.economic_assumptions.indices.obr.consumer_price_index"
RESIDENTIAL_PROPERTY_INPUTS = (
    "main_residence_value",
    "other_residential_property_value",
)


def _uprating_index_map() -> dict:
    with open(Path(__file__).parent / "uprating_indices.yaml", "r") as f:
        return yaml.safe_load(f)


def uprating_input_paths() -> list:
    """Every parameter path the dataset uprating reads.

    ``apply_single_year_uprating`` and the functions it calls read these, and
    no other parameters: the growth rates in ``uprating_indices.yaml``, the
    council tax and rent series, the cumulative residential property index,
    the conditional energy CPI index, the indices of the input variables that
    file leaves out (after ``LEGACY_PROJECTION_END_YEAR``) and the capital
    gains projection's metadata (``CGT_INDEX_PATH``). A path may name a node
    (the regional private rent series), which covers its parameters.
    """
    uprating = _uprating_index_map()
    series = {value for value in _COUNCIL_TAX_GROWTH_SERIES.values() if value}
    water_series = {value for value in _WATER_GROWTH_SERIES.values() if value}
    return sorted(
        set(uprating)
        | {f"{COUNCIL_TAX_GROWTH}.{name}" for name in series}
        | {f"{WATER_BILLS_GROWTH}.{name}" for name in water_series}
        | {
            SOCIAL_RENT_GROWTH,
            PRIVATE_RENT_GROWTH,
            CGT_INDEX_PATH,
            RESIDENTIAL_PROPERTY_INDEX,
            ENERGY_PRICE_INDEX,
        }
        | set(_unmapped_uprating_indices(uprating).values())
    )


def uprating_input_fingerprint(parameters: ParameterNode) -> str:
    """A digest of the parameter values the dataset uprating reads.

    Two parameter trees with the same fingerprint uprate a dataset
    identically, so an uprated dataset can be shared between them. It covers
    each read parameter's full timeline and the capital gains projection's
    metadata.
    """
    from policyengine_core.parameters import Parameter

    parts = []
    for path in uprating_input_paths():
        try:
            node = parameters.get_child(path)
        except ValueError:
            parts.append((path, None))
            continue
        leaves = (
            [node]
            if isinstance(node, Parameter)
            else [p for p in node.get_descendants() if isinstance(p, Parameter)]
        )
        for leaf in sorted(leaves, key=lambda leaf: leaf.name):
            parts.append(
                (
                    leaf.name,
                    tuple(
                        (entry.instant_str, repr(entry.value))
                        for entry in leaf.values_list
                    ),
                )
            )
        if path == CGT_INDEX_PATH:
            parts.append((path, repr((node.metadata or {}).get("projection"))))
    return hashlib.sha256(repr(parts).encode()).hexdigest()


def extend_single_year_dataset(
    dataset: UKSingleYearDataset,
    tax_benefit_system_parameters: ParameterNode,
    end_year: int | None = None,
) -> UKMultiYearDataset:
    """Project a supplied year to the shared default within any finite CGT span."""
    # A normalized legacy export still projects the original gross amount.
    dataset = legacy_projection_source(dataset)
    # Extend years and uprate
    start_year = int(dataset.time_period)
    if end_year is None:
        projection = tax_benefit_system_parameters.get_child(CGT_INDEX_PATH).metadata[
            "projection"
        ]
        end_year = max(
            start_year,
            min(PROJECTION_END_YEAR, projection.get("end_year", PROJECTION_END_YEAR)),
        )
    datasets = [dataset]
    for year in range(start_year, end_year + 1):
        next_year = dataset.copy()
        next_year.time_period = str(year)
        datasets.append(next_year)
    multi_year_dataset = UKMultiYearDataset(datasets=datasets)
    return apply_uprating(
        multi_year_dataset,
        tax_benefit_system_parameters=tax_benefit_system_parameters,
        copy=False,
    )


def apply_uprating(
    dataset: UKMultiYearDataset,
    tax_benefit_system_parameters: ParameterNode = None,
    copy: bool = True,
):
    from policyengine_uk.system import system

    if not isinstance(dataset, UKMultiYearDataset):
        raise TypeError("dataset must be of type UKMultiYearDataset.")

    if copy:
        dataset = dataset.copy()

    first_year = min(dataset.datasets.keys())
    for year in dataset.datasets.keys():
        if year == first_year:
            continue  # Don't uprate the first year
        current_year = dataset.datasets[year]
        prev_year = dataset.datasets[year - 1]
        apply_single_year_uprating(
            current_year,
            prev_year,
            tax_benefit_system_parameters,
            base_year=first_year,
        )
        # Core projects from the supplied observation in one multiplication.
        # Chaining annual stock projections can lose an exact band boundary
        # through intermediate float32 rounding, even with the same index.
        uprate_residential_property(
            current_year, dataset.datasets[first_year], tax_benefit_system_parameters
        )
        uprate_energy(
            current_year, dataset.datasets[first_year], tax_benefit_system_parameters
        )

    return dataset


def apply_single_year_uprating(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
    base_year: int | None = None,
):
    # Apply uprating to a single year dataset. base_year is the year the
    # projected data describe (apply_uprating passes the dataset's first
    # year); without it, the previous year is taken as that year.

    projection = parameters.get_child(CGT_INDEX_PATH).metadata["projection"]
    if "base_year" in projection and any(
        variable in previous_year.person.columns for variable in CGT_DATASET_INPUTS
    ):
        source_year = int(previous_year.time_period)
        target_year = int(current_year.time_period)
        if (
            not projection["base_year"]
            <= source_year
            < target_year
            <= projection["end_year"]
        ):
            raise ValueError(
                f"Capital gains projection {projection['name']!r} supports "
                f"{projection['base_year']}–{projection['end_year']}, "
                f"not {source_year}–{target_year}."
            )

    # Year-specific inputs are dropped from every projected year.
    for table_name in current_year.table_names:
        table = getattr(current_year, table_name)
        stored = [name for name in YEAR_SPECIFIC_INPUTS if name in table.columns]
        if stored:
            table.drop(columns=stored, inplace=True)

    # First, apply standard variable-YoY growth based uprating.

    savings_rule = uniform_savings_income_projection(
        [
            previous_year.savings_income_projection,
            current_year.savings_income_projection,
        ]
    )
    uprating = _uprating_index_map()
    for index_name, variables in uprating.items():
        index_rel_change = growth_rate(
            parameters, index_name, current_year.time_period, savings_rule
        )
        for variable in variables:
            for table_name, df in zip(current_year.table_names, current_year.tables):
                if variable in df.columns:
                    prev_year_value = getattr(previous_year, table_name)[variable]
                    split_bsp = (
                        variable == "bsp_reported"
                        and BEREAVEMENT_SPLIT_INPUTS.issubset(
                            previous_year.person.columns
                        )
                    )
                    current_year_value = (
                        prev_year_value
                        if split_bsp
                        else prev_year_value * (1 + index_rel_change)
                    )
                    getattr(current_year, table_name)[variable] = current_year_value

    if (
        current_year.isa_income_contract["projection"] == "legacy_gross"
        and SAVINGS_INTEREST in current_year.person
    ):
        growth = growth_rate(
            parameters, SAVINGS_INCOME_GROWTH, current_year.time_period, savings_rule
        )
        values = gross_interest(previous_year) * (1 + growth)
        if current_year.isa_income_contract["representation"] == "additive":
            values = values - effective_tax_free(current_year.person)
        current_year.person[SAVINGS_INTEREST] = values

    # New additive ISA receipts use the same dataset rule as ordinary
    # interest. Legacy receipts retain their former unindexed treatment.
    if (
        current_year.isa_income_contract["projection"] == "additive"
        and ISA_INTEREST in current_year.person
    ):
        growth = growth_rate(
            parameters, SAVINGS_INCOME_GROWTH, current_year.time_period, savings_rule
        )
        current_year.person[ISA_INTEREST] = previous_year.person[ISA_INTEREST] * (
            1 + growth
        )

    # Next, apply custom uprating.

    current_year = uprate_energy(current_year, previous_year, parameters)

    # apply_uprating replaces these chained stocks from the original observation.
    current_year = uprate_residential_property(current_year, previous_year, parameters)

    # Council Tax is uprated by OBR forecasts/outturns by country.

    current_year = uprate_council_tax(current_year, previous_year, parameters)

    # Water and sewerage charges are uprated by country.

    current_year = uprate_water_and_sewerage_charges(
        current_year, previous_year, parameters
    )

    # Rent is uprated by OBR forecasts/outturns by region.

    current_year = uprate_rent(current_year, previous_year, parameters)

    current_year = uprate_student_loan_plans(
        current_year, previous_year, parameters, base_year=base_year
    )

    # Stored arrays take precedence over Core's variable-level uprating.
    # Reproduce the index growth Core used after the old dataset horizon for
    # inputs missing from the projection map (for example salary sacrifice).
    if int(current_year.time_period) > LEGACY_PROJECTION_END_YEAR:
        for variable, index_name in _unmapped_uprating_indices(uprating).items():
            # Handled above for new additive data; deliberately unchanged for
            # legacy gross data, whose exemption never had this new index.
            if variable == ISA_INTEREST:
                continue
            for table_name in current_year.table_names:
                table = getattr(current_year, table_name)
                if variable in table.columns:
                    index = parameters.get_child(index_name)
                    previous_index = _uprating_index_value(
                        index, f"{previous_year.time_period}-01-01"
                    )
                    current_index = _uprating_index_value(
                        index, f"{current_year.time_period}-01-01"
                    )
                    # Use Core's treatment of missing, zero and explicitly
                    # terminated indices as well as its cumulative ratio.
                    ratio = (
                        current_index / previous_index
                        if previous_index not in (None, 0) and current_index is not None
                        else 1
                    )
                    table[variable] = (
                        getattr(previous_year, table_name)[variable] * ratio
                    )

    current_year.validate()

    return current_year


def uprate_energy(
    current_year: UKSingleYearDataset,
    observed_year: UKSingleYearDataset,
    parameters: ParameterNode,
) -> UKSingleYearDataset:
    """Project declared energy prices with the existing annual CPI assumption."""
    basis = observed_year.energy_price_basis
    variables = [
        name
        for name in DECLARED_ENERGY_INPUTS
        if name in observed_year.household.columns
        and name in current_year.household.columns
    ]
    ratio = 1
    projected = False
    if basis is not None and variables:
        index = parameters.get_child(ENERGY_PRICE_INDEX)
        source_instant = f"{basis['period_value']:04d}-01-01"
        target_instant = f"{int(current_year.time_period):04d}-01-01"
        supported_instants = [
            value.instant_str
            for value in getattr(index, "values_list", [])
            if value.value is not None
        ]
        if not supported_instants:
            raise ValueError(
                f"Energy index {ENERGY_PRICE_INDEX!r} has no non-null history "
                f"for declared basis {source_instant} and target {target_instant}."
            )
        first_supported = min(supported_instants)
        if source_instant < first_supported or target_instant < first_supported:
            raise ValueError(
                f"Energy index {ENERGY_PRICE_INDEX!r} first supports "
                f"{first_supported}; declared basis {source_instant} and target "
                f"{target_instant} must be on or after that instant."
            )
        source_index = _uprating_index_value(index, source_instant)
        target_index = _uprating_index_value(index, target_instant)
        projected = source_index not in (None, 0) and target_index is not None
        if projected:
            ratio = target_index / source_index
    for variable in variables:
        current_year.household[variable] = (
            observed_year.household[variable].to_numpy() * ratio
        )
    current_year.energy_price_basis = (
        {"period_type": "fiscal_year", "period_value": int(current_year.time_period)}
        if projected
        else basis
    )
    return current_year


def uprate_residential_property(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
):
    """Keep residential stocks on Core and HVCTS's cumulative HPI basis.

    Cumulative index levels are rounded when generated. Use one ratio from
    the supplied observation, at the variable's Core storage precision, so
    forward projection and inverse band conversion share the same basis.
    """
    from policyengine_uk.system import system

    assets = [
        name
        for name in RESIDENTIAL_PROPERTY_INPUTS
        if name in current_year.household.columns
    ]
    if not assets:
        return current_year
    index = parameters.get_child(RESIDENTIAL_PROPERTY_INDEX)
    previous_index = _uprating_index_value(index, f"{previous_year.time_period}-01-01")
    current_index = _uprating_index_value(index, f"{current_year.time_period}-01-01")
    # Preserve Core's handling of missing, zero and terminated indices.
    ratio = (
        current_index / previous_index
        if previous_index not in (None, 0) and current_index is not None
        else 1
    )
    for asset in assets:
        observed = previous_year.household[asset].to_numpy(
            dtype=system.variables[asset].dtype
        )
        current_year.household[asset] = observed * ratio
    return current_year


def household_weight_growth_path(uprating: dict | None = None) -> str:
    """The growth series that projects household weights.

    The one ``uprating_indices.yaml`` lists ``household_weight`` under.
    """
    uprating = _uprating_index_map() if uprating is None else uprating
    paths = [path for path, names in uprating.items() if "household_weight" in names]
    if len(paths) != 1:
        raise ValueError(
            "uprating_indices.yaml must list household_weight under exactly one "
            f"growth series, not {paths}"
        )
    return paths[0]


def uprate_council_tax(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
):
    # Uprate council tax for a single year dataset.
    #
    # Each country's series is the growth in its council tax receipts: the
    # Band D level times the tax base, the number of Band D equivalent
    # dwellings. Household weights grow too, by their own series, so each bill
    # grows by receipts growth net of the weights' growth. A country's
    # weighted total then grows by its receipts growth. Growing the bills by
    # receipts growth counted the growth in households twice (#2067).

    council_tax = parameters.gov.economic_assumptions.yoy_growth.obr.council_tax
    region = pd.Series(np.asarray(current_year.household["region"]).astype(str))
    unrecognised = set(region) - set(_COUNCIL_TAX_GROWTH_SERIES)
    if unrecognised:
        raise ValueError(
            "Cannot uprate council tax for unrecognised regions: "
            f"{sorted(unrecognised)}"
        )
    weight_growth = parameters.get_child(household_weight_growth_path())(
        current_year.time_period
    )
    factor_by_region = {
        name: 1.0
        if series is None
        else (1 + council_tax.get_child(series)(current_year.time_period))
        / (1 + weight_growth)
        for name, series in _COUNCIL_TAX_GROWTH_SERIES.items()
    }
    factors = region.map(factor_by_region).to_numpy()

    current_year.household["council_tax"] = (
        previous_year.household["council_tax"] * factors
    )
    if (
        "council_tax_benefit_reported" in previous_year.person.columns
        and "council_tax_benefit_reported" in current_year.person.columns
    ):
        # Keep reported reductions at the same share of their household bill.
        household_factors = pd.Series(
            factors, index=current_year.household["household_id"]
        )
        person_factors = previous_year.person["person_household_id"].map(
            household_factors
        )
        person = current_year.person.copy()
        person["council_tax_benefit_reported"] = (
            previous_year.person["council_tax_benefit_reported"].to_numpy()
            * person_factors.to_numpy()
        )
        current_year.person = person
    return current_year


def uprate_water_and_sewerage_charges(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
):
    # Uprate water and sewerage charges for a single year dataset, by country.

    if "water_and_sewerage_charges" not in previous_year.household.columns:
        return current_year
    region = pd.Series(np.asarray(current_year.household["region"]).astype(str))
    unrecognised = set(region) - set(_WATER_GROWTH_SERIES)
    if unrecognised:
        raise ValueError(
            "Cannot uprate water and sewerage charges for unrecognised regions: "
            f"{sorted(unrecognised)}"
        )
    growth_by_region = {}
    for name, series in _WATER_GROWTH_SERIES.items():
        rate = (
            None
            if series is None
            else parameters.get_child(f"{WATER_BILLS_GROWTH}.{series}")(
                current_year.time_period
            )
        )
        growth_by_region[name] = 0.0 if rate is None else rate
    growth_rates = region.map(growth_by_region).to_numpy()

    current_year.household["water_and_sewerage_charges"] = previous_year.household[
        "water_and_sewerage_charges"
    ] * (1 + growth_rates)
    return current_year


def uprate_rent(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
):
    # Uprate rent for a single year dataset.
    is_private_rented = current_year.household["tenure_type"] == "RENT_PRIVATELY"
    region = current_year.household["region"]
    prev_rent = previous_year.household["rent"]
    growth = parameters.gov.economic_assumptions.yoy_growth
    year = int(current_year.time_period)
    social_rent_growth = growth.obr.social_rent(year)

    if year < 2022:
        logging.warning(
            "Rent uprating is not supported for years before 2022. Not applying uprating."
        )
        pass
    else:
        # Region.UNKNOWN has no regional index of its own, so those households
        # take the UK-wide one.
        region_index = np.array(region.values.astype(str))
        region_index = np.where(
            region_index == "UNKNOWN", "UNITED_KINGDOM", region_index
        )
        private_rent_growth = growth.ons.private_rental_prices(year)[region_index]
        current_year.household["rent"] = np.where(
            is_private_rented,
            prev_rent * (1 + private_rent_growth),
            prev_rent * (1 + social_rent_growth),
        )

    return current_year


def uprate_student_loan_plans(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
    base_year: int | None = None,
) -> UKSingleYearDataset:
    """Retain observed student loan plans and add new entrants.

    Existing holders keep their recorded plan and the repayment amount passed
    to this helper. Course, funding and first-repayment dates are unavailable,
    so age and current residence cannot establish a different plan or a
    cancellation date. The enclosing uprating separately grows stored
    repayments with average earnings, which this helper does not change.

    Retaining recorded plans also leaves future cohort transitions from
    Plan 1 to Plan 2 in England and Wales at the 2012 intake, and from Plan 2
    to Plan 5 in England at the 2023 intake, unimplemented. Vahid Ahmadi's
    25 October 2026 review audit used enhanced_frs_2024_25 at revision
    2526edbb and the age-18 intake proxy. Among 7.14m recorded Plan 2 holders,
    it counted 0.53m in England whose proxy intake reached 2023 in 2026,
    1.57m in 2028 and 2.99m in 2031. Among 1.52m recorded Plan 1 holders,
    it counted none in England and Wales whose proxy intake reached 2012
    in 2025, 0.30m in 2028 and 0.68m in 2031. These approximate counts
    describe that reviewer's dataset audit; this change does not reproduce
    the audit or establish national population accuracy or revenue effects.
    See the audit and accepted follow-up scope:
    https://github.com/PolicyEngine/policyengine-uk/pull/2650#issuecomment-6396818516
    https://github.com/PolicyEngine/policyengine-uk/pull/2650#issuecomment-6397144626
    Date-aware cohort and cancellation work remains open under issue 2636.

    Projected datasets copy the base year with ages fixed. Each year's plans
    therefore start from that copy, not accumulated prior-year plan state.
    base_year is the year the data describe; without it, the previous year is
    taken as that year. This fallback can retain older plans too long and
    changes the future plan mix; it does not model exact cancellation dates.

    New entrants use the existing intake-at-18 approximation, year - age + 18,
    to extend the base year's age bands and add England's Plan 5 intakes.
    We use highest_education == TERTIARY as the signal for who is a graduate,
    then apply a flat take-up probability. Each person's take-up draw is keyed
    on person_id, so the same people take up a loan in every year and in any
    row order.

    New holders follow the funding nation's undergraduate repayment plan.
    Funding agency is unavailable in the dataset, so current household
    region proxies for it: England, Wales, SAAS for Scotland, and Student
    Finance NI for Northern Ireland. This cannot identify cross-border
    movers. An unknown region leaves the plan unchanged. See
    https://www.gov.uk/repaying-your-student-loan/which-repayment-plan-you-are-on.
    """
    # Skip if required columns don't exist yet (e.g., during
    # initial dataset creation before imputation runs)
    required = ("student_loan_plan", "highest_education", "person_id")
    if any(col not in current_year.person.columns for col in required):
        return current_year

    year = int(current_year.time_period)
    if base_year is None:
        base_year = int(previous_year.time_period)

    person = current_year.person.copy()
    household = current_year.household[["household_id", "region"]].copy()

    # Join region onto person via person_household_id.
    person = person.merge(
        household.rename(columns={"household_id": "person_household_id"}),
        on="person_household_id",
        how="left",
    )

    age = person["age"].values.astype(int)
    base_plan = person["student_loan_plan"].values.copy().astype(str)
    region = person["region"].values.astype(str)
    highest_ed = person["highest_education"].values.astype(str)

    uni_start_year = year - age + 18
    is_england = np.isin(region, list(_ENGLAND_REGIONS))
    is_wales = region == "WALES"
    is_scotland = region == "SCOTLAND"
    is_northern_ireland = region == "NORTHERN_IRELAND"
    is_tertiary = highest_ed == "TERTIARY"

    # England introduced Plan 5 in 2023; Wales kept Plan 2. SAAS and
    # Student Finance NI use Plans 4 and 1 respectively for all intakes.
    # Current residence is the funding-nation proxy described above.
    new_borrower_plan = np.select(
        [
            is_scotland,
            is_northern_ireland,
            is_england & (uni_start_year >= _PLAN5_FIRST_UNI_START),
            (is_england | is_wales) & (uni_start_year >= _PLAN2_FIRST_UNI_START),
            is_england | is_wales,
        ],
        ["PLAN_4", "PLAN_1", "PLAN_5", "PLAN_2", "PLAN_1"],
        default="NONE",
    )

    # Initialize output arrays
    new_plan = base_plan.copy()
    repayments = person["student_loan_repayments"].values.copy()

    # One draw per person, the same in every year.
    draws = splitmix64_uniform(person["person_id"].values, salt=_STUDENT_LOAN_DRAW_SALT)

    # Helper to assign plans to eligible people
    def assign_with_probability(mask, prob=_GRADUATE_LOAN_TAKE_UP):
        """Assign the funding-nation plan to sampled new borrowers."""
        sampled = mask & (draws < prob) & (new_borrower_plan != "NONE")
        new_plan[sampled] = new_borrower_plan[sampled]
        repayments[sampled] = 0.0

    # === Step 1: Retain observed loan holders ===
    # Missing course and repayment dates do not establish a new plan or a
    # cancellation. The initialized arrays retain each recorded non-NONE
    # plan and repayment; the intake and region proxies apply only below.

    # === Step 2: Add holders in the extended pre-2012 age bands ===
    # Income-contingent (Plan 1) loans began with the 1998 intake, aged 44 in
    # 2024. With ages fixed, later years' 1998-and-later intakes reach older
    # ages: in 2029, ages 45 to 49 (the 1998 to 2002 intakes).
    # Target: NONE people who are tertiary-educated, older than the base
    # year's oldest Plan 1 holder, from the 1998 to 2011 intakes, whose loan
    # is not written off: at 65 for the 2005 and earlier intakes, otherwise
    # about 29 years after the course started.
    max_plan1_age_base = base_year - _PLAN1_FIRST_UNI_START + 18
    plan1_written_off = np.where(
        uni_start_year <= _PLAN1_LAST_AGE_65_WRITEOFF_UNI_START,
        age >= _PLAN1_WRITEOFF_AGE,
        uni_start_year + _PLAN1_WRITEOFF_YEARS <= year,
    )
    plan1_new_cohort = (
        (new_plan == "NONE")
        & is_tertiary
        & (age > max_plan1_age_base)
        & (uni_start_year >= _PLAN1_FIRST_UNI_START)
        & (uni_start_year < _PLAN2_FIRST_UNI_START)
        & ~plan1_written_off
    )
    assign_with_probability(plan1_new_cohort)

    # === Step 3: Add holders in the extended 2012-2022 age bands ===
    # In the base year Plan 2 holders are at most the age of the 2012 intake
    # (30 in 2024). With ages fixed, by 2029 Plan 2 reaches age 35.
    # Target: NONE people who are tertiary-educated, older than the base
    # year's oldest Plan 2 holder, whose uni_start_year is 2012-2022.
    max_plan2_age_base = base_year - _PLAN2_FIRST_UNI_START + 18
    plan2_new_cohort = (
        (new_plan == "NONE")
        & is_tertiary
        & (age > max_plan2_age_base)
        & (uni_start_year >= _PLAN2_FIRST_UNI_START)
        & (uni_start_year < _PLAN5_FIRST_UNI_START)
    )
    assign_with_probability(plan2_new_cohort)

    # === Step 4: Add Plan 5 holders (new plan from 2023) ===
    # Plan 5 is England's, and did not exist in the base year. The other
    # nations' 2023-and-later intakes are on plans (2, 4 and 1) the base year
    # already holds at those ages, so no holders are added there.
    # Eligible: tertiary-educated NONE people in England who would have
    # started uni 2023+.
    # Age constraint: must be 21+ (finished 3-year degree) to be repaying.
    plan5_eligible = (
        (new_plan == "NONE")
        & is_tertiary
        & is_england
        & (uni_start_year >= _PLAN5_FIRST_UNI_START)
        & (age >= 21)
    )
    assign_with_probability(plan5_eligible)

    # Write back to the person table (without the merged region column).
    person_out = current_year.person.copy()
    person_out["student_loan_plan"] = new_plan
    person_out["student_loan_repayments"] = repayments
    current_year.person = person_out

    return current_year


def reset_uprating(
    dataset: UKMultiYearDataset,
):
    # Remove all uprating from the dataset.

    first_year = min(dataset.datasets.keys())
    for year in dataset.datasets:
        if year != first_year:
            dataset.datasets[year] = dataset.datasets[first_year].copy()
            dataset.datasets[year].time_period = str(year)

    return dataset


def reset_growthfactor_uprating(
    dataset: UKMultiYearDataset,
):
    uprating = _uprating_index_map()

    growthfactor_uprated_variables = {
        variable for variables in uprating.values() for variable in variables
    }
    growthfactor_uprated_variables.update(
        {"council_tax", "council_tax_benefit_reported", "rent", ISA_INTEREST}
    )
    growthfactor_uprated_variables.update(COUNTRY_UPRATED_INPUTS)
    growthfactor_uprated_variables.update(_unmapped_uprating_indices(uprating))
    growthfactor_uprated_variables.difference_update(DATASET_UPRATING_EXCLUSIONS)

    first_year = min(dataset.datasets.keys())
    base_year_dataset = dataset.datasets[first_year]
    base_energy = DECLARED_ENERGY_INPUTS.intersection(
        base_year_dataset.household.columns
    )

    for year in dataset.datasets:
        if year == first_year:
            continue
        current_year_dataset = dataset.datasets[year]
        current_energy = DECLARED_ENERGY_INPUTS.intersection(
            current_year_dataset.household.columns
        )
        shared_energy = current_energy.intersection(base_energy)
        replace_energy_group = bool(current_energy) and current_energy <= base_energy
        reset_energy = replace_energy_group or (
            current_year_dataset.energy_price_basis
            == base_year_dataset.energy_price_basis
        )
        preserve_bsp = BEREAVEMENT_SPLIT_INPUTS.issubset(
            base_year_dataset.person.columns
        ) or BEREAVEMENT_SPLIT_INPUTS.issubset(current_year_dataset.person.columns)

        # One declaration describes every stored energy amount. Keep the
        # later group intact if a partial reset would mix different bases.
        for table_name in current_year_dataset.table_names:
            base_table = getattr(base_year_dataset, table_name)
            current_table = getattr(current_year_dataset, table_name)
            for variable in growthfactor_uprated_variables:
                # Split BSP amounts do not reflect economic growth. In a
                # schema transition, the base amount can include other benefits.
                if variable == "bsp_reported" and preserve_bsp:
                    continue
                if variable in current_table.columns and variable in base_table.columns:
                    if (
                        variable == ISA_INTEREST
                        and current_year_dataset.isa_income_contract["projection"]
                        == "legacy_gross"
                    ):
                        continue
                    if variable == SAVINGS_INTEREST:
                        if (
                            current_year_dataset.isa_income_contract["projection"]
                            == "legacy_gross"
                        ):
                            values = gross_interest(base_year_dataset)
                            if (
                                current_year_dataset.isa_income_contract[
                                    "representation"
                                ]
                                == "additive"
                            ):
                                values = values - effective_tax_free(current_table)
                        else:
                            values = ordinary_interest(base_year_dataset)
                        current_table[variable] = values
                    else:
                        current_table[variable] = base_table[variable].values
        if reset_energy:
            for variable in shared_energy:
                current_year_dataset.household[variable] = base_year_dataset.household[
                    variable
                ].values
        if replace_energy_group:
            current_year_dataset.energy_price_basis = (
                base_year_dataset.energy_price_basis
            )

    return dataset
