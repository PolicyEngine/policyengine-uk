from policyengine_uk.model_api import *


class housing_benefit_non_dep_additional_exception(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Additional Housing Benefit non-dependant exemption"
    documentation = "Normal home elsewhere, specified youth training, under-25 income-related ESA outside the support/WRAG groups, and qualifying hospital, custody or military-operation absence. Student and postponed-increase rules are applied separately for each claimant."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dwp.housing_benefit.non_dep_deduction.additional_exceptions
        esa = (
            (person("age", period) < p.assessment_phase_age)
            & (person("esa_income_reported", period) > 0)
            & ~person("esa_support_group", period)
            & ~person("esa_work_related_activity_group", period)
        )
        hospital = person("is_hospital_inpatient", period) & (
            person("housing_benefit_non_dep_linked_inpatient_days", period)
            > p.hospital_weeks * 7
        )
        custody = person("is_in_prison", period) & person(
            "housing_benefit_non_dep_custody_excludes_mental_health_hospital", period
        )
        absence = person("housing_benefit_non_dep_absent", period) & (
            hospital
            | custody
            | person("housing_benefit_non_dep_military_operations", period)
        )
        return (
            person("housing_benefit_non_dep_normal_home_elsewhere", period)
            | person("housing_benefit_non_dep_youth_training_allowance", period)
            | esa
            | absence
        )
