from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country
from policyengine_uk.variables.household.demographic.locations import LocalAuthority


def is_england_pensioner_scheme(country, has_pensioner):
    return (country == Country.ENGLAND) & has_pensioner


def is_scotland_scheme(country):
    return country == Country.SCOTLAND


def is_wales_scheme(country):
    return country == Country.WALES


def is_merton(local_authority):
    return local_authority == LocalAuthority.MERTON


def is_merton_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_merton(local_authority)


def is_kingston_upon_thames(local_authority):
    return local_authority == LocalAuthority.KINGSTON_UPON_THAMES


def is_kingston_upon_thames_working_age(local_authority, country, has_pensioner):
    return (
        (country == Country.ENGLAND)
        & ~has_pensioner
        & is_kingston_upon_thames(local_authority)
    )


def is_newham(local_authority):
    return local_authority == LocalAuthority.NEWHAM


def is_newham_working_age(local_authority, country, has_pensioner):
    return (country == Country.ENGLAND) & ~has_pensioner & is_newham(local_authority)


def is_supported_scheme(country, has_pensioner, local_authority):
    return (
        is_england_pensioner_scheme(country, has_pensioner)
        | is_scotland_scheme(country)
        | is_wales_scheme(country)
        | is_merton_working_age(local_authority, country, has_pensioner)
        | is_kingston_upon_thames_working_age(local_authority, country, has_pensioner)
        | is_newham_working_age(local_authority, country, has_pensioner)
    )
