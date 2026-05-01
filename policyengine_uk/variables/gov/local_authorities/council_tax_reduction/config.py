from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country
from policyengine_uk.variables.household.demographic.locations import (
    LocalAuthority,
)
from policyengine_uk.variables.input.council_tax_band import CouncilTaxBand


def is_adur(local_authority):
    return local_authority == LocalAuthority.ADUR


def is_basingstoke_and_deane(local_authority):
    return local_authority == LocalAuthority.BASINGSTOKE_AND_DEANE


def is_dudley(local_authority):
    return local_authority == LocalAuthority.DUDLEY


def is_breckland(local_authority):
    return local_authority == LocalAuthority.BRECKLAND


def is_bolton(local_authority):
    return local_authority == LocalAuthority.BOLTON


def is_broadland(local_authority):
    return local_authority == LocalAuthority.BROADLAND


def is_chesterfield(local_authority):
    return local_authority == LocalAuthority.CHESTERFIELD


def is_crawley(local_authority):
    return local_authority == LocalAuthority.CRAWLEY


def is_east_hertfordshire(local_authority):
    return local_authority == LocalAuthority.EAST_HERTFORDSHIRE


def is_east_cambridgeshire(local_authority):
    return local_authority == LocalAuthority.EAST_CAMBRIDGESHIRE


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


def is_lancaster(local_authority):
    return local_authority == LocalAuthority.LANCASTER


def is_merton(local_authority):
    return local_authority == LocalAuthority.MERTON


def is_oldham(local_authority):
    return local_authority == LocalAuthority.OLDHAM


def is_norwich(local_authority):
    return local_authority == LocalAuthority.NORWICH


def is_north_norfolk(local_authority):
    return local_authority == LocalAuthority.NORTH_NORFOLK


def is_oxford(local_authority):
    return local_authority == LocalAuthority.OXFORD


def is_southwark(local_authority):
    return local_authority == LocalAuthority.SOUTHWARK


def is_south_norfolk(local_authority):
    return local_authority == LocalAuthority.SOUTH_NORFOLK


def is_sefton(local_authority):
    return local_authority == LocalAuthority.SEFTON


def is_st_albans(local_authority):
    return local_authority == LocalAuthority.ST_ALBANS


def is_warrington(local_authority):
    return local_authority == LocalAuthority.WARRINGTON


def is_west_suffolk(local_authority):
    return local_authority == LocalAuthority.WEST_SUFFOLK


def is_worthing(local_authority):
    return local_authority == LocalAuthority.WORTHING


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


def is_east_cambridgeshire_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_east_cambridgeshire(local_authority)
    )


def is_east_suffolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_east_suffolk(local_authority)
    )


def is_adur_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_adur(local_authority)


def is_basingstoke_and_deane_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_basingstoke_and_deane(local_authority)
    )


def is_breckland_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_breckland(local_authority)


def is_bolton_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_bolton(local_authority)


def is_broadland_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_broadland(local_authority)


def is_chesterfield_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_chesterfield(local_authority)
    )


def is_crawley_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_crawley(local_authority)


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


def is_lancaster_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_lancaster(local_authority)


def is_merton_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_merton(local_authority)


def is_oldham_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_oldham(local_authority)


def is_norwich_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_norwich(local_authority)


def is_north_norfolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_north_norfolk(local_authority)
    )


def is_oxford_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_oxford(local_authority)


def is_southwark_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_southwark(local_authority)


def is_south_norfolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_south_norfolk(local_authority)
    )


def is_sefton_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_sefton(local_authority)


def is_st_albans_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_st_albans(local_authority)


def is_warrington_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_warrington(local_authority)
    )


def is_west_suffolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_west_suffolk(local_authority)
    )


def is_worthing_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_worthing(local_authority)


def is_supported_scheme(local_authority, country, has_pensioner):
    return (
        is_england_pensioner_scheme(country, has_pensioner)
        | is_scotland_scheme(country)
        | is_wales_scheme(country)
        | is_adur_working_age(local_authority, country, has_pensioner)
        | is_basingstoke_and_deane_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_bolton_working_age(local_authority, country, has_pensioner)
        | is_breckland_working_age(local_authority, country, has_pensioner)
        | is_broadland_working_age(local_authority, country, has_pensioner)
        | is_chesterfield_working_age(local_authority, country, has_pensioner)
        | is_crawley_working_age(local_authority, country, has_pensioner)
        | is_east_cambridgeshire_working_age(
            local_authority,
            country,
            has_pensioner,
        )
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
        | is_lancaster_working_age(local_authority, country, has_pensioner)
        | is_merton_working_age(local_authority, country, has_pensioner)
        | is_oldham_working_age(local_authority, country, has_pensioner)
        | is_norwich_working_age(local_authority, country, has_pensioner)
        | is_north_norfolk_working_age(local_authority, country, has_pensioner)
        | is_oxford_working_age(local_authority, country, has_pensioner)
        | is_sefton_working_age(local_authority, country, has_pensioner)
        | is_south_norfolk_working_age(local_authority, country, has_pensioner)
        | is_southwark_working_age(local_authority, country, has_pensioner)
        | is_st_albans_working_age(local_authority, country, has_pensioner)
        | is_warrington_working_age(local_authority, country, has_pensioner)
        | is_west_suffolk_working_age(local_authority, country, has_pensioner)
        | is_worthing_working_age(local_authority, country, has_pensioner)
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
