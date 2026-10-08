from policyengine_uk.model_api import *


class housing_benefit_childcare_work_condition(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    label = "Housing Benefit childcare work condition"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        adult = person("is_claimant_or_partner", period)
        works = person("housing_benefit_childcare_treated_as_work", period)
        cannot_care = (
            person("housing_benefit_childcare_incapacitated", period)
            | person("is_hospital_inpatient", period)
            | person("is_in_prison", period)
        )
        working_adults = benunit.sum(adult & works)
        couple_qualifies = benunit.all(~adult | works | cannot_care) & (
            working_adults > 0
        )
        return where(
            benunit("is_couple", period),
            couple_qualifies,
            benunit("is_lone_parent", period) & (working_adults > 0),
        )
