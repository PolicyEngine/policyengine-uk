from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


def is_england_pensioner_scheme(country, has_pensioner):
    return (country == Country.ENGLAND) & has_pensioner


def is_scotland_scheme(country):
    return country == Country.SCOTLAND


def is_wales_scheme(country):
    return country == Country.WALES


def is_supported_scheme(country, has_pensioner):
    return (
        is_england_pensioner_scheme(country, has_pensioner)
        | is_scotland_scheme(country)
        | is_wales_scheme(country)
    )
