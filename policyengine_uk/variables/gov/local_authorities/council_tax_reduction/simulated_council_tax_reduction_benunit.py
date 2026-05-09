from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_england_pensioner_scheme,
    is_scotland_scheme,
    is_wales_scheme,
)


LOCAL_COUNCIL_TAX_REDUCTION_VARIABLES = [
    "adur_council_tax_reduction",
    "babergh_council_tax_reduction",
    "basildon_council_tax_reduction",
    "barking_and_dagenham_council_tax_reduction",
    "barnet_council_tax_reduction",
    "basingstoke_and_deane_council_tax_reduction",
    "bolton_council_tax_reduction",
    "breckland_council_tax_reduction",
    "brent_council_tax_reduction",
    "bromley_council_tax_reduction",
    "bristol_council_tax_reduction",
    "broadland_council_tax_reduction",
    "bury_council_tax_reduction",
    "buckinghamshire_council_tax_reduction",
    "camden_council_tax_reduction",
    "chelmsford_council_tax_reduction",
    "cheltenham_council_tax_reduction",
    "cheshire_west_and_chester_council_tax_reduction",
    "chichester_council_tax_reduction",
    "chesterfield_council_tax_reduction",
    "colchester_council_tax_reduction",
    "cotswold_council_tax_reduction",
    "coventry_council_tax_reduction",
    "crawley_council_tax_reduction",
    "croydon_council_tax_reduction",
    "cumberland_council_tax_reduction",
    "darlington_council_tax_reduction",
    "dudley_council_tax_reduction",
    "ealing_council_tax_reduction",
    "enfield_council_tax_reduction",
    "east_cambridgeshire_council_tax_reduction",
    "east_hertfordshire_council_tax_reduction",
    "east_suffolk_council_tax_reduction",
    "fenland_council_tax_reduction",
    "gateshead_council_tax_reduction",
    "greenwich_council_tax_reduction",
    "haringey_council_tax_reduction",
    "harrow_council_tax_reduction",
    "havering_council_tax_reduction",
    "herefordshire_council_tax_reduction",
    "hackney_council_tax_reduction",
    "hammersmith_and_fulham_council_tax_reduction",
    "hillingdon_council_tax_reduction",
    "hounslow_council_tax_reduction",
    "ipswich_council_tax_reduction",
    "kings_lynn_and_west_norfolk_council_tax_reduction",
    "kingston_upon_hull_council_tax_reduction",
    "kingston_upon_thames_council_tax_reduction",
    "islington_council_tax_reduction",
    "lambeth_council_tax_reduction",
    "lancaster_council_tax_reduction",
    "lewisham_council_tax_reduction",
    "merton_council_tax_reduction",
    "mid_suffolk_council_tax_reduction",
    "newham_council_tax_reduction",
    "oldham_council_tax_reduction",
    "north_norfolk_council_tax_reduction",
    "north_northamptonshire_council_tax_reduction",
    "north_yorkshire_council_tax_reduction",
    "norwich_council_tax_reduction",
    "oxford_council_tax_reduction",
    "plymouth_council_tax_reduction",
    "redbridge_council_tax_reduction",
    "sefton_council_tax_reduction",
    "somerset_council_tax_reduction",
    "slough_council_tax_reduction",
    "south_norfolk_council_tax_reduction",
    "southend_on_sea_council_tax_reduction",
    "southwark_council_tax_reduction",
    "st_albans_council_tax_reduction",
    "stockport_council_tax_reduction",
    "stevenage_council_tax_reduction",
    "stroud_council_tax_reduction",
    "tameside_council_tax_reduction",
    "thurrock_council_tax_reduction",
    "wakefield_council_tax_reduction",
    "warrington_council_tax_reduction",
    "west_suffolk_council_tax_reduction",
    "west_northamptonshire_council_tax_reduction",
    "westmorland_and_furness_council_tax_reduction",
    "westminster_council_tax_reduction",
    "worthing_council_tax_reduction",
]


class simulated_council_tax_reduction_benunit(Variable):
    value_type = float
    entity = BenUnit
    label = "Simulated Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        local_authority_parameters = parameters(period).gov.local_authorities
        england_pensioners_ctr = (
            local_authority_parameters.england.council_tax_reduction.pensioners
        )
        wales_ctr = local_authority_parameters.wales.council_tax_reduction
        scotland_ctr = local_authority_parameters.scotland.council_tax_reduction
        local_ctr = add(benunit, period, LOCAL_COUNCIL_TAX_REDUCTION_VARIABLES)
        is_household_head_benunit = benunit("benunit_contains_household_head", period)
        would_claim = benunit("would_claim_council_tax_reduction", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        babergh_local_scheme = benunit(
            "babergh_council_tax_reduction_is_local_scheme", period
        )
        basildon_local_scheme = benunit(
            "basildon_council_tax_reduction_is_local_scheme", period
        )
        buckinghamshire_local_scheme = benunit(
            "buckinghamshire_council_tax_reduction_is_local_scheme", period
        )
        chelmsford_local_scheme = benunit(
            "chelmsford_council_tax_reduction_is_local_scheme", period
        )
        cheltenham_local_scheme = benunit(
            "cheltenham_council_tax_reduction_is_local_scheme", period
        )
        cheshire_west_and_chester_local_scheme = benunit(
            "cheshire_west_and_chester_council_tax_reduction_is_local_scheme", period
        )
        chichester_local_scheme = benunit(
            "chichester_council_tax_reduction_is_local_scheme", period
        )
        colchester_local_scheme = benunit(
            "colchester_council_tax_reduction_is_local_scheme", period
        )
        cotswold_local_scheme = benunit(
            "cotswold_council_tax_reduction_is_local_scheme", period
        )
        coventry_local_scheme = benunit(
            "coventry_council_tax_reduction_is_local_scheme", period
        )
        herefordshire_local_scheme = benunit(
            "herefordshire_council_tax_reduction_is_local_scheme", period
        )
        kingston_upon_hull_local_scheme = benunit(
            "kingston_upon_hull_council_tax_reduction_is_local_scheme", period
        )
        ipswich_local_scheme = benunit(
            "ipswich_council_tax_reduction_is_local_scheme", period
        )
        mid_suffolk_local_scheme = benunit(
            "mid_suffolk_council_tax_reduction_is_local_scheme", period
        )
        north_yorkshire_local_scheme = benunit(
            "north_yorkshire_council_tax_reduction_is_local_scheme", period
        )
        plymouth_local_scheme = benunit(
            "plymouth_council_tax_reduction_is_local_scheme", period
        )
        somerset_local_scheme = benunit(
            "somerset_council_tax_reduction_is_local_scheme", period
        )
        slough_local_scheme = benunit(
            "slough_council_tax_reduction_is_local_scheme", period
        )
        southend_on_sea_local_scheme = benunit(
            "southend_on_sea_council_tax_reduction_is_local_scheme", period
        )
        thurrock_local_scheme = benunit(
            "thurrock_council_tax_reduction_is_local_scheme", period
        )
        west_northamptonshire_local_scheme = benunit(
            "west_northamptonshire_council_tax_reduction_is_local_scheme",
            period,
        )
        westmorland_and_furness_local_scheme = benunit(
            "westmorland_and_furness_council_tax_reduction_is_local_scheme",
            period,
        )
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit("council_tax_reduction_applicable_income", period)

        england_pensioners = (
            is_england_pensioner_scheme(country, has_pensioner)
            & ~babergh_local_scheme
            & ~basildon_local_scheme
            & ~buckinghamshire_local_scheme
            & ~chelmsford_local_scheme
            & ~cheltenham_local_scheme
            & ~cheshire_west_and_chester_local_scheme
            & ~chichester_local_scheme
            & ~colchester_local_scheme
            & ~cotswold_local_scheme
            & ~coventry_local_scheme
            & ~herefordshire_local_scheme
            & ~ipswich_local_scheme
            & ~kingston_upon_hull_local_scheme
            & ~mid_suffolk_local_scheme
            & ~north_yorkshire_local_scheme
            & ~plymouth_local_scheme
            & ~somerset_local_scheme
            & ~slough_local_scheme
            & ~southend_on_sea_local_scheme
            & ~thurrock_local_scheme
            & ~west_northamptonshire_local_scheme
            & ~westmorland_and_furness_local_scheme
        )
        wales = is_wales_scheme(country)
        scotland = is_scotland_scheme(country)
        national_scheme = england_pensioners | wales | scotland
        max_support = select(
            [
                england_pensioners,
                wales,
                scotland,
            ],
            [
                england_pensioners_ctr.maximum_support_rate,
                wales_ctr.maximum_support_rate,
                scotland_ctr.maximum_support_rate,
            ],
            default=0.0,
        )
        liability = benunit.household(
            "council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit("council_tax_reduction_non_dep_deductions", period)
        withdrawal_rate = select(
            [
                england_pensioners,
                wales,
                scotland,
            ],
            [
                england_pensioners_ctr.means_test.withdrawal_rate,
                wales_ctr.means_test.withdrawal_rate,
                scotland_ctr.means_test.withdrawal_rate,
            ],
            default=0.0,
        )
        capital_limit = select(
            [
                england_pensioners,
                wales,
                scotland,
            ],
            [
                england_pensioners_ctr.means_test.capital_limit,
                wales_ctr.means_test.capital_limit,
                scotland_ctr.means_test.capital_limit,
            ],
            default=0.0,
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        preliminary_award = max_(
            0,
            liability * max_support
            - excess_income * withdrawal_rate
            - non_dep_deductions,
        )
        capital_eligible = benunit.household("savings", period) <= capital_limit
        national_ctr = (
            national_scheme
            * is_household_head_benunit
            * would_claim
            * capital_eligible
            * preliminary_award
        )
        return national_ctr + local_ctr
