from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country
from policyengine_uk.variables.household.demographic.locations import (
    LocalAuthority,
)
from policyengine_uk.variables.input.council_tax_band import CouncilTaxBand


def is_dudley(local_authority):
    return local_authority == LocalAuthority.DUDLEY


def is_east_hertfordshire(local_authority):
    return local_authority == LocalAuthority.EAST_HERTFORDSHIRE


def is_stroud(local_authority):
    return local_authority == LocalAuthority.STROUD


def is_warrington(local_authority):
    return local_authority == LocalAuthority.WARRINGTON


def is_england_pensioner_scheme(country, has_pensioner):
    return (country == Country.ENGLAND) & has_pensioner


def is_scotland_scheme(country):
    return country == Country.SCOTLAND


def is_wales_scheme(country):
    return country == Country.WALES


def is_east_hertfordshire_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_east_hertfordshire(local_authority)
    )


def is_stroud_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_stroud(local_authority)


def is_warrington_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_warrington(local_authority)
    )


def is_supported_scheme(local_authority, country, has_pensioner):
    return (
        is_england_pensioner_scheme(country, has_pensioner)
        | is_scotland_scheme(country)
        | is_wales_scheme(country)
        | is_east_hertfordshire_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_stroud_working_age(local_authority, country, has_pensioner)
        | is_warrington_working_age(local_authority, country, has_pensioner)
        | is_dudley_working_age(local_authority, country, has_pensioner)
    )


def is_dudley_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_dudley(local_authority)


def english_council_tax_band_ratio(council_tax_band, band_ratios):
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
        [
            band_ratios.A,
            band_ratios.B,
            band_ratios.C,
            band_ratios.D,
            band_ratios.E,
            band_ratios.F,
            band_ratios.G,
            band_ratios.H,
            band_ratios.I,
        ],
        default=band_ratios.D,
    )
