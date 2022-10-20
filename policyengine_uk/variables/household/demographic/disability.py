from policyengine_uk.model_api import *


class is_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Has a disability"
    documentation = "Whether this person is disabled for benefits purposes"
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "dla",
            "pip",
        ]
        return add(person, period, QUALIFYING_BENEFITS) > 0


class is_enhanced_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Whether meets the middle disability benefit entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        DLA_requirement = (
            parameters(period).gov.dwp.dla.self_care.higher * WEEKS_IN_YEAR
        )
        return person("dla_sc", period) >= DLA_requirement


class is_severely_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Has a severe disability"
    documentation = (
        "Whether this person is severely disabled for benefits purposes"
    )
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        benefit = parameters(period).gov.dwp
        THRESHOLD_SAFETY_GAP = 10 * WEEKS_IN_YEAR
        paragraph_3 = (
            person("dla_sc", period)
            >= benefit.dla.self_care.higher * WEEKS_IN_YEAR
            - THRESHOLD_SAFETY_GAP
        )
        paragraph_4 = (
            person("pip_dl", period)
            >= benefit.pip.daily_living.enhanced * WEEKS_IN_YEAR
            - THRESHOLD_SAFETY_GAP
        )
        paragraph_5 = person("AFCS", period) > 0
        return sum([paragraph_3, paragraph_4, paragraph_5]) > 0


class num_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        disabled = benunit.members("is_disabled_for_benefits", period)
        return benunit.sum(child & disabled)


class num_enhanced_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of enhanced disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        enhanced_disabled = benunit.members(
            "is_enhanced_disabled_for_benefits", period
        )
        return benunit.sum(child & enhanced_disabled)


class num_severely_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of severely disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        severely_disabled = benunit.members(
            "is_severely_disabled_for_benefits", period
        )
        return benunit.sum(child & severely_disabled)


class num_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of disabled adults"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        disabled = benunit.members("is_disabled_for_benefits", period)
        return benunit.sum(adult & disabled)


class num_enhanced_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of enhanced disabled adults"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        enhanced_disabled = benunit.members(
            "is_enhanced_disabled_for_benefits", period
        )
        return benunit.sum(adult & enhanced_disabled)


class num_severely_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of severely disabled adults"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        severely_disabled = benunit.members(
            "is_severely_disabled_for_benefits", period
        )
        return benunit.sum(adult & severely_disabled)


class disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Disability premium"
    definition_period = YEAR
    reference = "The Social Security Amendment (Enhanced Disability Premium) Regulations 2000"
    unit = GBP

    def formula(benunit, period, parameters):
        dis = parameters(period).gov.dwp.disability_premia
        single = benunit("is_single", period.this_year)
        couple = benunit("is_couple", period.this_year)
        single_premium = single * dis.disability_single
        couple_premium = couple * dis.disability_couple
        has_disabled_adults = (
            benunit("num_disabled_adults", period.this_year) > 0
        )
        weekly_amount = single_premium + couple_premium
        return weekly_amount * WEEKS_IN_YEAR * has_disabled_adults


class severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Severe disability premium"
    definition_period = YEAR
    reference = "The Social Security Amendment (Enhanced Disability Premium) Regulations 2000"
    unit = GBP

    def formula(benunit, period, parameters):
        dis = parameters(period).gov.dwp.disability_premia
        single = benunit("is_single", period.this_year)
        couple = benunit("is_couple", period.this_year)
        single_premium = single * dis.severe_single
        couple_premium = couple * dis.severe_couple
        has_severely_disabled_adults = (
            benunit("num_severely_disabled_adults", period.this_year) > 0
        )
        weekly_amount = single_premium + couple_premium
        return weekly_amount * WEEKS_IN_YEAR * has_severely_disabled_adults


class enhanced_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Enhanced disability premium"
    definition_period = YEAR
    reference = "The Social Security Amendment (Enhanced Disability Premium) Regulations 2000"
    unit = GBP

    def formula(benunit, period, parameters):
        dis = parameters(period).gov.dwp.disability_premia
        single = benunit("is_single", period.this_year)
        couple = benunit("is_couple", period.this_year)
        single_premium = single * dis.enhanced_single
        couple_premium = couple * dis.enhanced_couple
        has_enhanced_disabled_adults = (
            benunit("num_enhanced_disabled_adults", period.this_year) > 0
        )
        weekly_amount = single_premium + couple_premium
        return weekly_amount * WEEKS_IN_YEAR * has_enhanced_disabled_adults
