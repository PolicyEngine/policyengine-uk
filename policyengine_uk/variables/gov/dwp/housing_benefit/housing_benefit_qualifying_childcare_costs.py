from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day
from policyengine_uk.utils.housing_benefit import september_first_monday


class housing_benefit_qualifying_childcare_costs(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = GBP
    label = "Qualifying Housing Benefit childcare charges for this child"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.childcare
        born = birth_day(person, period)
        assessment = person.benunit("housing_benefit_assessment_date", period)
        disabled = (
            (
                add(person, period, ["dla", "pip", "armed_forces_independence_payment"])
                > 0
            )
            | person("housing_benefit_childcare_disability_benefit_in_payment", period)
            | person(
                "housing_benefit_childcare_disability_payment_suspended_in_hospital",
                period,
            )
            | person("is_blind", period)
        )
        ceased = person("housing_benefit_childcare_blind_certification_ceased", period)
        standard_end = september_first_monday(born, p.child_age_limit.standard - 1)
        disabled_end = september_first_monday(born, p.child_age_limit.disabled - 1)
        blind_weeks = parameters(period).gov.dwp.housing_benefit.blindness_run_on_weeks
        recent_blind = (
            (ceased >= standard_end - np.timedelta64(int(blind_weeks * 7), "D"))
            & (ceased < disabled_end)
            & (ceased <= assessment)
        )
        age_end = where(disabled | recent_blind, disabled_end, standard_end)
        child = person("is_child_or_young_person_for_legacy_benefits", period)
        provider = person("housing_benefit_childcare_provider", period)
        types = provider.possible_values
        home = person("housing_benefit_childcare_in_child_home", period)
        relative = person("housing_benefit_childcare_provider_is_relative", period)
        ordinary_provider = (
            (provider == types.REGISTERED_APPROVED)
            | (provider == types.EXEMPT_SCHOOL)
            | (provider == types.FOSTER_KINSHIP_OTHER_CHILD)
            | (provider == types.DOMICILIARY_WORKER)
        )
        school_route = (provider == types.SCHOOL_LOCAL_AUTHORITY_OUT_OF_HOURS) & (
            person("age", period) >= p.out_of_school_min_age
        )
        home_route = (provider == types.NON_RELATIVE_HOME_CARE) & home & ~relative
        provider_qualifies = (
            (ordinary_provider | school_route | home_route)
            & ~(relative & home)
            & ~person("housing_benefit_childcare_paid_to_partner", period)
        )
        charges = max_(
            person("housing_benefit_childcare_charges_paid", period)
            - person("housing_benefit_childcare_compulsory_education_charges", period),
            0,
        )
        return where(child & (assessment < age_end) & provider_qualifies, charges, 0)
