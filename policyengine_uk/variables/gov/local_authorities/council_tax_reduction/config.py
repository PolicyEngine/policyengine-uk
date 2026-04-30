from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country
from policyengine_uk.variables.household.demographic.locations import (
    LocalAuthority,
)
from policyengine_uk.variables.input.council_tax_band import CouncilTaxBand


def is_dudley(local_authority):
    return local_authority == LocalAuthority.DUDLEY


def is_breckland(local_authority):
    return local_authority == LocalAuthority.BRECKLAND


def is_chesterfield(local_authority):
    return local_authority == LocalAuthority.CHESTERFIELD


def is_east_hertfordshire(local_authority):
    return local_authority == LocalAuthority.EAST_HERTFORDSHIRE


def is_east_suffolk(local_authority):
    return local_authority == LocalAuthority.EAST_SUFFOLK


def is_stevenage(local_authority):
    return local_authority == LocalAuthority.STEVENAGE


def is_stroud(local_authority):
    return local_authority == LocalAuthority.STROUD


def is_darlington(local_authority):
    return local_authority == LocalAuthority.DARLINGTON


def is_gateshead(local_authority):
    return local_authority == LocalAuthority.GATESHEAD


def is_fenland(local_authority):
    return local_authority == LocalAuthority.FENLAND


def is_kings_lynn_and_west_norfolk(local_authority):
    return local_authority == LocalAuthority.KINGS_LYNN_AND_WEST_NORFOLK


def is_merton(local_authority):
    return local_authority == LocalAuthority.MERTON


def is_norwich(local_authority):
    return local_authority == LocalAuthority.NORWICH


def is_north_norfolk(local_authority):
    return local_authority == LocalAuthority.NORTH_NORFOLK


def is_southwark(local_authority):
    return local_authority == LocalAuthority.SOUTHWARK


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


def is_east_suffolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_east_suffolk(local_authority)
    )


def is_breckland_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_breckland(local_authority)


def is_chesterfield_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_chesterfield(local_authority)
    )


def is_stevenage_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_stevenage(local_authority)


def is_stroud_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_stroud(local_authority)


def is_darlington_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_darlington(local_authority)
    )


def is_gateshead_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_gateshead(local_authority)


def is_fenland_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_fenland(local_authority)


def is_kings_lynn_and_west_norfolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_kings_lynn_and_west_norfolk(local_authority)
    )


def is_merton_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_merton(local_authority)


def is_norwich_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_norwich(local_authority)


def is_north_norfolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_north_norfolk(local_authority)
    )


def is_southwark_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_southwark(local_authority)


def is_warrington_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_warrington(local_authority)
    )


def is_supported_scheme(local_authority, country, has_pensioner):
    return (
        is_england_pensioner_scheme(country, has_pensioner)
        | is_scotland_scheme(country)
        | is_wales_scheme(country)
        | is_breckland_working_age(local_authority, country, has_pensioner)
        | is_chesterfield_working_age(local_authority, country, has_pensioner)
        | is_east_hertfordshire_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_east_suffolk_working_age(local_authority, country, has_pensioner)
        | is_fenland_working_age(local_authority, country, has_pensioner)
        | is_stevenage_working_age(local_authority, country, has_pensioner)
        | is_stroud_working_age(local_authority, country, has_pensioner)
        | is_darlington_working_age(local_authority, country, has_pensioner)
        | is_gateshead_working_age(local_authority, country, has_pensioner)
        | is_kings_lynn_and_west_norfolk_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_merton_working_age(local_authority, country, has_pensioner)
        | is_norwich_working_age(local_authority, country, has_pensioner)
        | is_north_norfolk_working_age(local_authority, country, has_pensioner)
        | is_southwark_working_age(local_authority, country, has_pensioner)
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
