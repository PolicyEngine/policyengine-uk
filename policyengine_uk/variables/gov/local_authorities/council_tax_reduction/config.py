from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country
from policyengine_uk.variables.household.demographic.locations import (
    LocalAuthority,
)
from policyengine_uk.variables.input.council_tax_band import CouncilTaxBand


def is_adur(local_authority):
    return local_authority == LocalAuthority.ADUR


def is_babergh(local_authority):
    return local_authority == LocalAuthority.BABERGH


def is_basingstoke_and_deane(local_authority):
    return local_authority == LocalAuthority.BASINGSTOKE_AND_DEANE


def is_barking_and_dagenham(local_authority):
    return local_authority == LocalAuthority.BARKING_AND_DAGENHAM


def is_barnet(local_authority):
    return local_authority == LocalAuthority.BARNET


def is_dudley(local_authority):
    return local_authority == LocalAuthority.DUDLEY


def is_breckland(local_authority):
    return local_authority == LocalAuthority.BRECKLAND


def is_brent(local_authority):
    return local_authority == LocalAuthority.BRENT


def is_bromley(local_authority):
    return local_authority == LocalAuthority.BROMLEY


def is_bristol(local_authority):
    return local_authority == LocalAuthority.BRISTOL


def is_bolton(local_authority):
    return local_authority == LocalAuthority.BOLTON


def is_broadland(local_authority):
    return local_authority == LocalAuthority.BROADLAND


def is_bury(local_authority):
    return local_authority == LocalAuthority.BURY


def is_buckinghamshire(local_authority):
    return local_authority == LocalAuthority.BUCKINGHAMSHIRE


def is_camden(local_authority):
    return local_authority == LocalAuthority.CAMDEN


def is_chesterfield(local_authority):
    return local_authority == LocalAuthority.CHESTERFIELD


def is_crawley(local_authority):
    return local_authority == LocalAuthority.CRAWLEY


def is_croydon(local_authority):
    return local_authority == LocalAuthority.CROYDON


def is_cumberland(local_authority):
    return local_authority == LocalAuthority.CUMBERLAND


def is_ealing(local_authority):
    return local_authority == LocalAuthority.EALING


def is_enfield(local_authority):
    return local_authority == LocalAuthority.ENFIELD


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


def is_greenwich(local_authority):
    return local_authority == LocalAuthority.GREENWICH


def is_haringey(local_authority):
    return local_authority == LocalAuthority.HARINGEY


def is_harrow(local_authority):
    return local_authority == LocalAuthority.HARROW


def is_havering(local_authority):
    return local_authority == LocalAuthority.HAVERING


def is_herefordshire(local_authority):
    return local_authority == LocalAuthority.HEREFORDSHIRE


def is_hackney(local_authority):
    return local_authority == LocalAuthority.HACKNEY


def is_hammersmith_and_fulham(local_authority):
    return local_authority == LocalAuthority.HAMMERSMITH_AND_FULHAM


def is_hillingdon(local_authority):
    return local_authority == LocalAuthority.HILLINGDON


def is_hounslow(local_authority):
    return local_authority == LocalAuthority.HOUNSLOW


def is_fenland(local_authority):
    return local_authority == LocalAuthority.FENLAND


def is_kings_lynn_and_west_norfolk(local_authority):
    return local_authority == LocalAuthority.KINGS_LYNN_AND_WEST_NORFOLK


def is_kingston_upon_hull(local_authority):
    return (local_authority == LocalAuthority.KINGSTON_UPON_HULL) | (
        local_authority == LocalAuthority.KINGSTON_UPON_HULL_CITY_OF
    )


def is_kingston_upon_thames(local_authority):
    return local_authority == LocalAuthority.KINGSTON_UPON_THAMES


def is_islington(local_authority):
    return local_authority == LocalAuthority.ISLINGTON


def is_lambeth(local_authority):
    return local_authority == LocalAuthority.LAMBETH


def is_lancaster(local_authority):
    return local_authority == LocalAuthority.LANCASTER


def is_lewisham(local_authority):
    return local_authority == LocalAuthority.LEWISHAM


def is_merton(local_authority):
    return local_authority == LocalAuthority.MERTON


def is_mid_suffolk(local_authority):
    return local_authority == LocalAuthority.MID_SUFFOLK


def is_newham(local_authority):
    return local_authority == LocalAuthority.NEWHAM


def is_oldham(local_authority):
    return local_authority == LocalAuthority.OLDHAM


def is_norwich(local_authority):
    return local_authority == LocalAuthority.NORWICH


def is_north_norfolk(local_authority):
    return local_authority == LocalAuthority.NORTH_NORFOLK


def is_north_northamptonshire(local_authority):
    return local_authority == LocalAuthority.NORTH_NORTHAMPTONSHIRE


def is_north_yorkshire(local_authority):
    return local_authority == LocalAuthority.NORTH_YORKSHIRE


def is_oxford(local_authority):
    return local_authority == LocalAuthority.OXFORD


def is_redbridge(local_authority):
    return local_authority == LocalAuthority.REDBRIDGE


def is_southwark(local_authority):
    return local_authority == LocalAuthority.SOUTHWARK


def is_somerset(local_authority):
    return local_authority == LocalAuthority.SOMERSET


def is_south_norfolk(local_authority):
    return local_authority == LocalAuthority.SOUTH_NORFOLK


def is_sefton(local_authority):
    return local_authority == LocalAuthority.SEFTON


def is_st_albans(local_authority):
    return local_authority == LocalAuthority.ST_ALBANS


def is_stockport(local_authority):
    return local_authority == LocalAuthority.STOCKPORT


def is_tameside(local_authority):
    return local_authority == LocalAuthority.TAMESIDE


def is_warrington(local_authority):
    return local_authority == LocalAuthority.WARRINGTON


def is_wakefield(local_authority):
    return local_authority == LocalAuthority.WAKEFIELD


def is_west_suffolk(local_authority):
    return local_authority == LocalAuthority.WEST_SUFFOLK


def is_westmorland_and_furness(local_authority):
    return local_authority == LocalAuthority.WESTMORLAND_AND_FURNESS


def is_west_northamptonshire(local_authority):
    return local_authority == LocalAuthority.WEST_NORTHAMPTONSHIRE


def is_westminster(local_authority):
    return local_authority == LocalAuthority.WESTMINSTER


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


def is_barking_and_dagenham_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_barking_and_dagenham(local_authority)
    )


def is_barnet_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_barnet(local_authority)


def is_babergh_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_babergh(local_authority)


def is_breckland_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_breckland(local_authority)


def is_brent_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_brent(local_authority)


def is_bromley_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_bromley(local_authority)


def is_bristol_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_bristol(local_authority)


def is_bolton_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_bolton(local_authority)


def is_broadland_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_broadland(local_authority)


def is_bury_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_bury(local_authority)


def is_buckinghamshire_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_buckinghamshire(local_authority)
    )


def is_camden_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_camden(local_authority)


def is_chesterfield_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_chesterfield(local_authority)
    )


def is_crawley_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_crawley(local_authority)


def is_croydon_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_croydon(local_authority)


def is_cumberland_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_cumberland(local_authority)
    )


def is_ealing_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_ealing(local_authority)


def is_enfield_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_enfield(local_authority)


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


def is_greenwich_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_greenwich(local_authority)


def is_haringey_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_haringey(local_authority)


def is_harrow_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_harrow(local_authority)


def is_havering_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_havering(local_authority)


def is_herefordshire_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_herefordshire(local_authority)
    )


def is_hackney_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_hackney(local_authority)


def is_hammersmith_and_fulham_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_hammersmith_and_fulham(local_authority)
    )


def is_hillingdon_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_hillingdon(local_authority)
    )


def is_hounslow_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_hounslow(local_authority)


def is_fenland_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_fenland(local_authority)


def is_kings_lynn_and_west_norfolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_kings_lynn_and_west_norfolk(local_authority)
    )


def is_kingston_upon_hull_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_kingston_upon_hull(local_authority)
    )


def is_kingston_upon_thames_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_kingston_upon_thames(local_authority)
    )


def is_islington_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_islington(local_authority)


def is_lambeth_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_lambeth(local_authority)


def is_lancaster_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_lancaster(local_authority)


def is_lewisham_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_lewisham(local_authority)


def is_merton_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_merton(local_authority)


def is_mid_suffolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_mid_suffolk(local_authority)
    )


def is_newham_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_newham(local_authority)


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


def is_north_northamptonshire_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_north_northamptonshire(local_authority)
    )


def is_north_yorkshire_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_north_yorkshire(local_authority)
    )


def is_oxford_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_oxford(local_authority)


def is_redbridge_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_redbridge(local_authority)


def is_southwark_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_southwark(local_authority)


def is_somerset_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_somerset(local_authority)


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


def is_stockport_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_stockport(local_authority)


def is_tameside_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_tameside(local_authority)


def is_warrington_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_warrington(local_authority)
    )


def is_wakefield_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_wakefield(local_authority)


def is_west_suffolk_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_west_suffolk(local_authority)
    )


def is_westmorland_and_furness_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_westmorland_and_furness(local_authority)
    )


def is_west_northamptonshire_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_west_northamptonshire(local_authority)
    )


def is_westminster_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND) & ~has_pensioner & is_westminster(local_authority)
    )


def is_worthing_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_worthing(local_authority)


def is_supported_scheme(local_authority, country, has_pensioner):
    return (
        is_england_pensioner_scheme(country, has_pensioner)
        | is_scotland_scheme(country)
        | is_wales_scheme(country)
        | is_adur_working_age(local_authority, country, has_pensioner)
        | is_babergh_working_age(local_authority, country, has_pensioner)
        | is_basingstoke_and_deane_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_barking_and_dagenham_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_barnet_working_age(local_authority, country, has_pensioner)
        | is_bolton_working_age(local_authority, country, has_pensioner)
        | is_breckland_working_age(local_authority, country, has_pensioner)
        | is_brent_working_age(local_authority, country, has_pensioner)
        | is_bromley_working_age(local_authority, country, has_pensioner)
        | is_bristol_working_age(local_authority, country, has_pensioner)
        | is_broadland_working_age(local_authority, country, has_pensioner)
        | is_bury_working_age(local_authority, country, has_pensioner)
        | is_buckinghamshire_working_age(local_authority, country, has_pensioner)
        | is_camden_working_age(local_authority, country, has_pensioner)
        | is_chesterfield_working_age(local_authority, country, has_pensioner)
        | is_crawley_working_age(local_authority, country, has_pensioner)
        | is_croydon_working_age(local_authority, country, has_pensioner)
        | is_cumberland_working_age(local_authority, country, has_pensioner)
        | is_ealing_working_age(local_authority, country, has_pensioner)
        | is_enfield_working_age(local_authority, country, has_pensioner)
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
        | is_greenwich_working_age(local_authority, country, has_pensioner)
        | is_haringey_working_age(local_authority, country, has_pensioner)
        | is_harrow_working_age(local_authority, country, has_pensioner)
        | is_havering_working_age(local_authority, country, has_pensioner)
        | is_herefordshire_working_age(local_authority, country, has_pensioner)
        | is_hackney_working_age(local_authority, country, has_pensioner)
        | is_hammersmith_and_fulham_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_hillingdon_working_age(local_authority, country, has_pensioner)
        | is_hounslow_working_age(local_authority, country, has_pensioner)
        | is_kings_lynn_and_west_norfolk_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_kingston_upon_hull_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_kingston_upon_thames_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        | is_islington_working_age(local_authority, country, has_pensioner)
        | is_lambeth_working_age(local_authority, country, has_pensioner)
        | is_lancaster_working_age(local_authority, country, has_pensioner)
        | is_lewisham_working_age(local_authority, country, has_pensioner)
        | is_merton_working_age(local_authority, country, has_pensioner)
        | is_mid_suffolk_working_age(local_authority, country, has_pensioner)
        | is_newham_working_age(local_authority, country, has_pensioner)
        | is_oldham_working_age(local_authority, country, has_pensioner)
        | is_norwich_working_age(local_authority, country, has_pensioner)
        | is_north_norfolk_working_age(local_authority, country, has_pensioner)
        | is_north_northamptonshire_working_age(local_authority, country, has_pensioner)
        | is_north_yorkshire_working_age(local_authority, country, has_pensioner)
        | is_oxford_working_age(local_authority, country, has_pensioner)
        | is_redbridge_working_age(local_authority, country, has_pensioner)
        | is_sefton_working_age(local_authority, country, has_pensioner)
        | is_somerset_working_age(local_authority, country, has_pensioner)
        | is_south_norfolk_working_age(local_authority, country, has_pensioner)
        | is_southwark_working_age(local_authority, country, has_pensioner)
        | is_st_albans_working_age(local_authority, country, has_pensioner)
        | is_stockport_working_age(local_authority, country, has_pensioner)
        | is_tameside_working_age(local_authority, country, has_pensioner)
        | is_warrington_working_age(local_authority, country, has_pensioner)
        | is_wakefield_working_age(local_authority, country, has_pensioner)
        | is_west_suffolk_working_age(local_authority, country, has_pensioner)
        | is_westmorland_and_furness_working_age(
            local_authority, country, has_pensioner
        )
        | is_west_northamptonshire_working_age(local_authority, country, has_pensioner)
        | is_westminster_working_age(local_authority, country, has_pensioner)
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
