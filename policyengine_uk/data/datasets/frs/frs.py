from typing import List
from policyengine_core.data import PrivateDataset, Dataset
import h5py
import logging
import pandas as pd
from pandas import DataFrame
import numpy as np
from policyengine_uk.data.datasets.frs.raw_frs import RawFRS
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER

max_ = np.maximum
where = np.where


class FRS(PrivateDataset):
    name = "frs"
    label = "FRS"
    folder_path = policyengine_uk_MICRODATA_FOLDER
    is_openfisca_compatible = True
    data_format = Dataset.ARRAYS

    filename_by_year = {
        2019: "frs_2019.h5",
    }

    def generate(self, year: int):
        if year in self.years:
            self.remove(year)
        # Load raw FRS tables
        year = int(year)

        if len(RawFRS.years) == 0:
            raise FileNotFoundError(
                "Raw FRS not found. Please run `openfisca-uk data raw_frs generate [year]` first."
            )

        if year > max(RawFRS.years):
            logging.warning("Uprating a previous version of the FRS.")
            if len(self.years) == 0:
                self.generate(max(RawFRS.years))
            if len(FRS.years) > 0:
                frs_year = max(self.years)
                from policyengine_uk import Microsimulation

                sim = Microsimulation(
                    dataset=self, dataset_year=max(self.years)
                )
                frs = h5py.File(self.file(year), mode="w")
                for variable in self.keys(frs_year):
                    frs[variable] = sim.calc(variable).values
                frs.close()
                return

        raw_frs_files = RawFRS.load(year)
        frs = h5py.File(self.file(year), mode="w")
        logging.info("Generating FRS dataset for year {}".format(year))
        logging.info("Loading FRS tables")
        TABLES = (
            "adult",
            "child",
            "accounts",
            "benefits",
            "job",
            "oddjob",
            "benunit",
            "househol",
            "chldcare",
            "pension",
            "maint",
            "mortgage",
            "penprov",
        )
        (
            adult,
            child,
            accounts,
            benefits,
            job,
            oddjob,
            benunit,
            household,
            childcare,
            pension,
            maintenance,
            mortgage,
            pen_prov,
        ) = [raw_frs_files[table] for table in TABLES]
        raw_frs_files.close()

        logging.info("Joining adult and child tables")

        person = pd.concat([adult, child]).sort_index().fillna(0)

        # Generate OpenFisca-UK variables and save
        logging.info("Generating OpenFisca-UK variables")
        add_id_variables(frs, person, benunit, household)
        add_personal_variables(frs, person)
        add_benunit_variables(frs, benunit)
        add_household_variables(frs, household)
        add_market_income(
            frs, person, pension, job, accounts, household, oddjob, year
        )
        add_benefit_income(frs, person, benefits, household)
        add_expenses(
            frs,
            person,
            job,
            household,
            maintenance,
            mortgage,
            childcare,
            pen_prov,
        )
        frs.close()
        logging.info("Completed FRS generation")


FRS = FRS()


def sum_to_entity(
    values: pd.Series, foreign_key: pd.Series, primary_key
) -> pd.Series:
    """Sums values by joining foreign and primary keys.

    Args:
        values (pd.Series): The values in the non-entity table.
        foreign_key (pd.Series): E.g. pension.person_id.
        primary_key ([type]): E.g. person.index.

    Returns:
        pd.Series: A value for each person.
    """
    return values.groupby(foreign_key).sum().reindex(primary_key).fillna(0)


def categorical(
    values: pd.Series, default: int, left: list, right: list
) -> pd.Series:
    """Maps a categorical input to an output using given left and right arrays.

    Args:
        values (pd.Series): The input values.
        default (int): A default value (to replace NaNs).
        left (list): The left side of the map.
        right (list): The right side of the map.

    Returns:
        pd.Series: The mapped values.
    """
    return (
        values.fillna(default)
        .map({i: j for i, j in zip(left, right)})
        .astype("S")
    )


def add_id_variables(
    frs: h5py.File, person: DataFrame, benunit: DataFrame, household: DataFrame
):
    """Adds ID variables and weights.

    Args:
        frs (h5py.File)
        person (DataFrame)
        benunit (DataFrame)
        household (DataFrame)
    """
    # Add primary and foreign keys
    frs["person_id"] = person.index
    frs["person_benunit_id"] = person.benunit_id
    frs["person_household_id"] = person.household_id
    frs["benunit_id"] = person.benunit_id.sort_values().unique()
    frs["household_id"] = person.household_id.sort_values().unique()

    # Add grossing weights
    frs["household_weight"] = household.GROSS4


def add_personal_variables(frs: h5py.File, person: DataFrame):
    """Adds personal variables (age, gender, education).

    Args:
        frs (h5py.File)
        person (DataFrame)
    """
    # Add basic personal variables
    age = person.AGE80 + person.AGE
    frs["age"] = age
    # Age fields are AGE80 (top-coded) and AGE in the adult and child tables, respectively.
    frs["state_id"] = np.array([1])
    frs["person_state_id"] = np.array([1] * len(person))
    frs["person_state_role"] = np.array(["member"] * len(person)).astype("S")
    frs["state_weight"] = np.array([1])
    frs["gender"] = np.where(person.SEX == 1, "MALE", "FEMALE").astype("S")
    frs["hours_worked"] = person.TOTHOURS * 52
    frs["is_household_head"] = person.HRPID == 1
    frs["is_benunit_head"] = person.UPERSON == 1
    MARITAL = [
        "MARRIED",
        "SINGLE",
        "SINGLE",
        "WIDOWED",
        "SEPARATED",
        "DIVORCED",
    ]
    frs["marital_status"] = categorical(
        person.MARITAL, 2, range(1, 7), MARITAL
    )

    # Add education levels
    fted = person.FTED
    typeed2 = person.TYPEED2
    frs["current_education"] = np.select(
        [
            fted.isin((2, -1, 0)),  # By default, not in education
            typeed2 == 1,  # In pre-primary
            typeed2.isin((2, 4))  # In primary, or...
            | (
                typeed2.isin((3, 8)) & (age < 11)
            )  # special or private education (and under 11), or...
            | (
                (typeed2 == 0) & (fted == 1) & (age > 5) & (age < 11)
            ),  # not given, full-time and between 5 and 11
            typeed2.isin((5, 6))  # In secondary, or...
            | (
                typeed2.isin((3, 8)) & (age >= 11) & (age <= 16)
            )  # special/private and meets age criteria, or...
            | (
                (typeed2 == 0) & (fted == 1) & (age <= 16)
            ),  # not given, full-time and under 17
            typeed2  # Non-advanced further education, or...
            == 7
            | (
                typeed2.isin((3, 8)) & (age > 16)
            )  # special/private and meets age criteria, or...
            | (
                (typeed2 == 0) & (fted == 1) & (age > 16)
            ),  # not given, full-time and over 16
            typeed2.isin((7, 8)) & (age >= 19),  # In post-secondary
            typeed2
            == 9
            | (
                (typeed2 == 0) & (fted == 1) & (age >= 19)
            ),  # In tertiary, or meets age condition
        ],
        [
            "NOT_IN_EDUCATION",
            "PRE_PRIMARY",
            "PRIMARY",
            "LOWER_SECONDARY",
            "UPPER_SECONDARY",
            "POST_SECONDARY",
            "TERTIARY",
        ],
    ).astype("S")

    # Add employment status
    EMPLOYMENTS = [
        "CHILD",
        "FT_EMPLOYED",
        "PT_EMPLOYED",
        "FT_SELF_EMPLOYED",
        "PT_SELF_EMPLOYED",
        "UNEMPLOYED",
        "RETIRED",
        "STUDENT",
        "CARER",
        "LONG_TERM_DISABLED",
        "SHORT_TERM_DISABLED",
    ]
    frs["employment_status"] = categorical(
        person.EMPSTATI, 1, range(12), EMPLOYMENTS
    )


def add_household_variables(frs: h5py.File, household: DataFrame):
    """Adds household variables (region, tenure, council tax imputation).

    Args:
        frs (h5py.File)
        household (DataFrame)
    """
    # Add region
    from policyengine_uk.variables.household.demographic.household import (
        Region,
    )

    REGIONS = [
        "NORTH_EAST",
        "NORTH_WEST",
        "YORKSHIRE",
        "EAST_MIDLANDS",
        "WEST_MIDLANDS",
        "EAST_OF_ENGLAND",
        "LONDON",
        "SOUTH_EAST",
        "SOUTH_WEST",
        "WALES",
        "SCOTLAND",
        "NORTHERN_IRELAND",
        "UNKNOWN",
    ]
    frs["region"] = categorical(
        household.GVTREGNO, 14, [1, 2] + list(range(4, 15)), REGIONS
    )
    TENURES = [
        "RENT_FROM_COUNCIL",
        "RENT_FROM_HA",
        "RENT_PRIVATELY",
        "RENT_PRIVATELY",
        "OWNED_OUTRIGHT",
        "OWNED_WITH_MORTGAGE",
    ]
    frs["tenure_type"] = categorical(
        household.PTENTYP2, 3, range(1, 7), TENURES
    )
    frs["num_bedrooms"] = household.BEDROOM6
    ACCOMMODATIONS = [
        "HOUSE_DETACHED",
        "HOUSE_SEMI_DETACHED",
        "HOUSE_TERRACED",
        "FLAT",
        "CONVERTED_HOUSE",
        "MOBILE",
        "OTHER",
    ]
    frs["accommodation_type"] = categorical(
        household.TYPEACC, 1, range(1, 8), ACCOMMODATIONS
    )

    # Impute Council Tax

    # Only ~25% of household report Council Tax bills - use
    # these to build a model to impute missing values
    CT_valid = household.CTANNUAL > 0

    # Find the mean reported Council Tax bill for a given
    # (region, CT band, is-single-person-household) triplet
    region = household.GVTREGNO[CT_valid]
    band = household.CTBAND[CT_valid]
    single_person = (household.ADULTH == 1)[CT_valid]
    ctannual = household.CTANNUAL[CT_valid]

    # Build the table
    CT_mean = ctannual.groupby(
        [region, band, single_person], dropna=False
    ).mean()
    CT_mean = CT_mean.replace(-1, CT_mean.mean())

    # For every household consult the table to find the imputed
    # Council Tax bill
    pairs = household.set_index(
        [household.GVTREGNO, household.CTBAND, (household.ADULTH == 1)]
    )
    hh_CT_mean = pd.Series(index=pairs.index)
    has_mean = pairs.index.isin(CT_mean.index)
    hh_CT_mean[has_mean] = CT_mean[pairs.index[has_mean]].values
    hh_CT_mean[~has_mean] = 0
    CT_imputed = hh_CT_mean

    # For households which originally reported Council Tax,
    # use the reported value. Otherwise, use the imputed value
    council_tax = pd.Series(
        np.where(
            # 2018 FRS uses blanks for missing values, 2019 FRS
            # uses -1 for missing values
            (household.CTANNUAL < 0) | household.CTANNUAL.isna(),
            max_(CT_imputed, 0).values,
            household.CTANNUAL,
        )
    )
    frs["council_tax"] = council_tax.fillna(0)
    BANDS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
    # Band 1 is the most common
    frs["council_tax_band"] = categorical(
        household.CTBAND, 1, range(1, 10), BANDS
    )
    # Domestic rates variables are all weeklyised, unlike Council Tax variables (despite the variable name suggesting otherwise)
    frs["domestic_rates"] = (
        np.select(
            [
                household.RTANNUAL >= 0,
                household.RT2REBAM >= 0,
                True,
            ],
            [
                household.RTANNUAL,
                household.RT2REBAM,
                0,
            ],
        )
        * 52
    )


def add_market_income(
    frs: h5py.File,
    person: DataFrame,
    pension: DataFrame,
    job: DataFrame,
    account: DataFrame,
    household: DataFrame,
    oddjob: DataFrame,
    year: DataFrame,
):
    """Adds income variables (non-benefit).

    Args:
        frs (h5py.File)
        person (DataFrame)
        pension (DataFrame)
        job (DataFrame)
        account (DataFrame)
        household (DataFrame)
        oddjob (DataFrame)
        year (DataFrame)
    """
    frs["employment_income"] = person.INEARNS * 52

    pension_payment = sum_to_entity(
        pension.PENPAY * (pension.PENPAY > 0), pension.person_id, person.index
    )
    pension_tax_paid = sum_to_entity(
        (pension.PTAMT * ((pension.PTINC == 2) & (pension.PTAMT > 0))),
        pension.person_id,
        person.index,
    )
    pension_deductions_removed = sum_to_entity(
        pension.POAMT
        * (
            ((pension.POINC == 2) | (pension.PENOTH == 1))
            & (pension.POAMT > 0)
        ),
        pension.person_id,
        person.index,
    )

    frs["pension_income"] = (
        pension_payment + pension_tax_paid + pension_deductions_removed
    ) * 52

    # Add self-employed income (correcting one person in 2018)
    INCORRECT_VALUES_PERSON_ID = 806911
    seincamt = sum_to_entity(job.SEINCAMT, job.person_id, person.index)
    frs["self_employment_income"] = (
        np.where(
            (year == 2018) & (person.index == INCORRECT_VALUES_PERSON_ID),
            seincamt,
            person.SEINCAM2,
        )
        * 52
    )

    INVERTED_BASIC_RATE = 1.25

    frs["tax_free_savings_income"] = (
        sum_to_entity(
            account.ACCINT * (account.ACCOUNT == 21),
            account.person_id,
            person.index,
        )
        * 52
    )
    taxable_savings_interest = (
        sum_to_entity(
            (
                account.ACCINT
                * np.where(account.ACCTAX == 1, INVERTED_BASIC_RATE, 1)
            )
            * (account.ACCOUNT.isin((1, 3, 5, 27, 28))),
            account.person_id,
            person.index,
        )
        * 52
    )
    frs["savings_interest_income"] = (
        taxable_savings_interest + frs["tax_free_savings_income"][...]
    )
    frs["dividend_income"] = (
        sum_to_entity(
            (
                account.ACCINT
                * np.where(account.INVTAX == 1, INVERTED_BASIC_RATE, 1)
            )
            * (
                ((account.ACCOUNT == 6) & (account.INVTAX == 1))  # GGES
                | account.ACCOUNT.isin((7, 8))  # Stocks/shares/UITs
            ),
            account.person_id,
            person.index,
        )
        * 52
    )
    is_head = person.HRPID == 1
    household_property_income = (
        household.TENTYP2.isin((5, 6)) * household.SUBRENT
    )  # Owned and subletting
    persons_household_property_income = pd.Series(
        household_property_income[person.household_id].values,
        index=person.index,
    ).fillna(0)
    frs["property_income"] = (
        max_(
            0,
            is_head * persons_household_property_income
            + person.CVPAY
            + person.ROYYR1,
        )
        * 52
    )

    # Discrepancy in maintenance income (UKMOD appears to use last amount rather than usual, with "not usual" answer):

    INVERTED_USUAL_AMOUNT_HOUSEHOLDS = (
        1458600,
        1033500,
        322100,
        42100,
        590400,
        645300,
        1901400,
        388000,
    )
    maintenance_to_self = max_(
        pd.Series(
            where(person.MNTUS1 == 2, person.MNTUSAM1, person.MNTAMT1)
        ).fillna(0),
        0,
    )
    use_DWP_usual_amount = (person.MNTUS2 == 2) & ~(
        (year == 2018)
        & (person.household_id.isin(INVERTED_USUAL_AMOUNT_HOUSEHOLDS))
    )
    maintenance_from_DWP = pd.Series(
        where(use_DWP_usual_amount, person.MNTUSAM2, person.MNTAMT2)
    )
    frs["maintenance_income"] = (
        sum_positive_variables([maintenance_to_self, maintenance_from_DWP])
        * 52
    )

    odd_job_income = sum_to_entity(
        oddjob.OJAMT * (oddjob.OJNOW == 1), oddjob.person_id, person.index
    )

    MISC_INCOME_FIELDS = [
        "ALLPAY2",
        "ROYYR2",
        "ROYYR3",
        "ROYYR4",
        "CHAMTERN",
        "CHAMTTST",
    ]

    frs["miscellaneous_income"] = (
        odd_job_income + sum_from_positive_fields(person, MISC_INCOME_FIELDS)
    ) * 52

    PRIVATE_TRANSFER_INCOME_FIELDS = [
        "APAMT",
        "APDAMT",
        "PAREAMT",
        "ALLPAY1",
        "ALLPAY3",
        "ALLPAY4",
    ]

    frs["private_transfer_income"] = (
        sum_from_positive_fields(person, PRIVATE_TRANSFER_INCOME_FIELDS) * 52
    )

    frs["lump_sum_income"] = person.REDAMT


def sum_from_positive_fields(
    table: pd.DataFrame, fields: List[str]
) -> np.array:
    """Sum from fields in table, ignoring negative values.

    Args:
        table (DataFrame)
        fields (List[str])

    Returns:
        np.array
    """
    return np.where(
        table[fields].sum(axis=1) > 0, table[fields].sum(axis=1), 0
    )


def sum_positive_variables(variables: List[str]) -> np.array:
    """Sum positive variables.

    Args:
        variables (List[str])

    Returns:
        np.array
    """
    return sum([np.where(variable > 0, variable, 0) for variable in variables])


def fill_with_mean(
    table: pd.DataFrame, code: str, amount: str, multiplier: float = 52
) -> np.array:
    """Fills missing values in a table with the mean of the column.

    Args:
        table (DataFrame): Table to fill.
        code (str): Column signifying existence.
        amount (str): Column with values.
        multiplier (float): Multiplier to apply to amount.

    Returns:
        np.array: Filled values.
    """
    needs_fill = (table[code] == 1) & (table[amount] < 0)
    has_value = (table[code] == 1) & (table[amount] >= 0)
    fill_mean = table[amount][has_value].mean()
    filled_values = np.where(needs_fill, fill_mean, table[amount])
    return np.maximum(filled_values, 0) * multiplier


def add_benefit_income(
    frs: h5py.File,
    person: DataFrame,
    benefits: DataFrame,
    household: DataFrame,
):
    """Adds benefit variables.

    Args:
        frs (h5py.File)
        person (DataFrame)
        benefits (DataFrame)
        household (DataFrame)
    """
    BENEFIT_CODES = dict(
        child_benefit=3,
        income_support=19,
        housing_benefit=94,
        AA=12,
        DLA_SC=1,
        DLA_M=2,
        IIDB=15,
        carers_allowance=13,
        SDA=10,
        AFCS=8,
        maternity_allowance=21,
        ssmg=22,
        pension_credit=4,
        child_tax_credit=91,
        working_tax_credit=90,
        state_pension=5,
        winter_fuel_allowance=62,
        incapacity_benefit=17,
        universal_credit=95,
        PIP_M=97,
        PIP_DL=96,
    )

    for benefit, code in BENEFIT_CODES.items():
        frs[benefit + "_reported"] = (
            sum_to_entity(
                benefits.BENAMT * (benefits.BENEFIT == code),
                benefits.person_id,
                person.index,
            )
            * 52
        )

    frs["JSA_contrib_reported"] = (
        sum_to_entity(
            benefits.BENAMT
            * (benefits.VAR2.isin((1, 3)))
            * (benefits.BENEFIT == 14),
            benefits.person_id,
            person.index,
        )
        * 52
    )
    frs["JSA_income_reported"] = (
        sum_to_entity(
            benefits.BENAMT
            * (benefits.VAR2.isin((2, 4)))
            * (benefits.BENEFIT == 14),
            benefits.person_id,
            person.index,
        )
        * 52
    )
    frs["ESA_contrib_reported"] = (
        sum_to_entity(
            benefits.BENAMT
            * (benefits.VAR2.isin((1, 3)))
            * (benefits.BENEFIT == 16),
            benefits.person_id,
            person.index,
        )
        * 52
    )
    frs["ESA_income_reported"] = (
        sum_to_entity(
            benefits.BENAMT
            * (benefits.VAR2.isin((2, 4)))
            * (benefits.BENEFIT == 16),
            benefits.person_id,
            person.index,
        )
        * 52
    )

    frs["BSP_reported"] = (
        sum_to_entity(
            benefits.BENAMT * (benefits.BENEFIT.isin((6, 9))),
            benefits.person_id,
            person.index,
        )
        * 52
    )

    frs["winter_fuel_allowance_reported"][...] = (
        np.array(frs["winter_fuel_allowance_reported"]) / 52
    )

    frs["SSP"] = person.SSPADJ * 52
    frs["SMP"] = person.SMPADJ * 52

    frs["student_loans"] = np.maximum(person.TUBORR, 0)

    frs["adult_ema"] = fill_with_mean(person, "ADEMA", "ADEMAAMT")
    frs["child_ema"] = fill_with_mean(person, "CHEMA", "CHEMAAMT")

    frs["access_fund"] = np.maximum(person.ACCSSAMT, 0) * 52

    frs["education_grants"] = np.maximum(
        person[["GRTDIR1", "GRTDIR2"]].sum(axis=1), 0
    )

    frs["council_tax_benefit_reported"] = np.maximum(
        (person.HRPID == 1)
        * pd.Series(
            household.CTREBAMT[person.household_id].values, index=person.index
        ).fillna(0)
        * 52,
        0,
    )


def add_expenses(
    frs: h5py.File,
    person: DataFrame,
    job: DataFrame,
    household: DataFrame,
    maintenance: DataFrame,
    mortgage: DataFrame,
    childcare: DataFrame,
    pen_prov: DataFrame,
):
    """Adds expense variables

    Args:
        frs (h5py.File)
        person (DataFrame)
        household (DataFrame)
        maintenance (DataFrame)
        mortgage (DataFrame)
        childcare (DataFrame)
        pen_prov (DataFrame)
    """
    frs["maintenance_expenses"] = (
        pd.Series(
            np.where(
                maintenance.MRUS == 2, maintenance.MRUAMT, maintenance.MRAMT
            )
        )
        .groupby(maintenance.person_id)
        .sum()
        .reindex(person.index)
        .fillna(0)
        * 52
    )

    frs["housing_costs"] = (
        np.where(
            household.GVTREGNO != 13, household.GBHSCOST, household.NIHSCOST
        )
        * 52
    )
    frs["rent"] = household.HHRENT.fillna(0) * 52
    frs["mortgage_interest_repayment"] = household.MORTINT.fillna(0) * 52
    mortgage_capital = np.where(
        mortgage.RMORT == 1, mortgage.RMAMT, mortgage.BORRAMT
    )
    mortgage_capital_repayment = sum_to_entity(
        mortgage_capital / mortgage.MORTEND,
        mortgage.household_id,
        household.index,
    )
    frs["mortgage_capital_repayment"] = mortgage_capital_repayment

    frs["childcare_expenses"] = (
        sum_to_entity(
            childcare.CHAMT
            * (childcare.COST == 1)
            * (childcare.REGISTRD == 1),
            childcare.person_id,
            person.index,
        )
        * 52
    )

    frs["private_pension_contributions"] = max_(
        0,
        sum_to_entity(
            pen_prov.PENAMT[pen_prov.STEMPPEN.isin((5, 6))],
            pen_prov.person_id,
            person.index,
        ).clip(0, pen_prov.PENAMT.quantile(0.95))
        * 52,
    )
    frs["occupational_pension_contributions"] = max_(
        0,
        sum_to_entity(job.DEDUC1.fillna(0), job.person_id, person.index) * 52,
    )

    frs["housing_service_charges"] = (
        pd.DataFrame(
            [
                household[f"CHRGAMT{i}"] * (household[f"CHRGAMT{i}"] > 0)
                for i in range(1, 10)
            ]
        ).sum()
        * 52
    )
    frs["water_and_sewerage_charges"] = (
        pd.Series(
            np.where(
                household.GVTREGNO == 12,
                household.CSEWAMT + household.CWATAMTD,
                household.WATSEWRT,
            )
        ).fillna(0)
        * 52
    )


def add_benunit_variables(frs: h5py.File, benunit: DataFrame):
    frs["benunit_rent"] = np.maximum(benunit.BURENT.fillna(0) * 52, 0)
