from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country
from policyengine_uk.variables.household.demographic.locations import (
    LocalAuthority,
)
from policyengine_uk.variables.input.council_tax_band import CouncilTaxBand

CLASSIC_MAX_SUPPORT_RATE = 1.0
CLASSIC_WITHDRAWAL_RATE = 0.2
DUDLEY_WORKING_AGE_MAX_SUPPORT_RATE = 0.4
DUDLEY_WORKING_AGE_NON_DEP_WEEKLY_DEDUCTION = 5.0
CAPITAL_LIMIT_GBP = 16_000

ENGLISH_BAND_C_RATIO = 8 / 9


def is_dudley(local_authority):
    return local_authority == LocalAuthority.DUDLEY


def is_stroud(local_authority):
    return local_authority == LocalAuthority.STROUD


def is_classic_scheme(local_authority, country, has_pensioner):
    return (
        (country == Country.SCOTLAND)
        | (country == Country.WALES)
        | ((country == Country.ENGLAND) & has_pensioner)
        | is_stroud(local_authority)
    )


def is_supported_scheme(local_authority, country, has_pensioner):
    return is_classic_scheme(local_authority, country, has_pensioner) | (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_dudley(local_authority)
    )


def maximum_support_rate(local_authority, country, has_pensioner):
    classic = is_classic_scheme(local_authority, country, has_pensioner)
    dudley = (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_dudley(local_authority)
    )
    return select(
        [classic, dudley],
        [CLASSIC_MAX_SUPPORT_RATE, DUDLEY_WORKING_AGE_MAX_SUPPORT_RATE],
        default=0.0,
    )


def english_council_tax_band_ratio(council_tax_band):
    return select(
        [
            council_tax_band == CouncilTaxBand.A,
            council_tax_band == CouncilTaxBand.B,
            council_tax_band == CouncilTaxBand.C,
            council_tax_band == CouncilTaxBand.D,
            council_tax_band == CouncilTaxBand.E,
            council_tax_band == CouncilTaxBand.F,
            council_tax_band == CouncilTaxBand.G,
            council_tax_band == CouncilTaxBand.H,
            council_tax_band == CouncilTaxBand.I,
        ],
        [6 / 9, 7 / 9, 8 / 9, 1.0, 11 / 9, 13 / 9, 15 / 9, 18 / 9, 21 / 9],
        default=1.0,
    )
