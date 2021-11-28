from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class is_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = u"Has a disability"
    documentation = "Whether this person is disabled for benefits purposes"
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "DLA_M",
            "DLA_SC",
            "PIP_M",
            "PIP_DL",
        ]
        return add(person, period, QUALIFYING_BENEFITS) > 0


class is_enhanced_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = u"Whether meets the middle disability benefit entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        DLA_requirement = (
            parameters(period).benefit.DLA.self_care.highest * WEEKS_IN_YEAR
        )
        sufficient_DLA = person("DLA_SC", period) >= DLA_requirement
        return sufficient_DLA


class is_severely_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = u"Has a severe disability"
    documentation = (
        "Whether this person is severely disabled for benefits purposes"
    )
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        benefit = parameters(period).benefit
        THRESHOLD_SAFETY_GAP = 10 * WEEKS_IN_YEAR
        paragraph_3 = (
            person("DLA_SC", period)
            >= benefit.DLA.self_care.highest * WEEKS_IN_YEAR
            - THRESHOLD_SAFETY_GAP
        )
        paragraph_4 = (
            person("PIP_DL", period)
            >= benefit.PIP.daily_living.higher * WEEKS_IN_YEAR
            - THRESHOLD_SAFETY_GAP
        )
        paragraph_5 = person("AFCS", period) > 0
        return sum([paragraph_3, paragraph_4, paragraph_5]) > 0


class num_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        disabled = benunit.members("is_disabled_for_benefits", period) > 0
        return benunit.sum(child * disabled)


class num_enhanced_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of enhanced disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        disabled = (
            benunit.members("is_enhanced_disabled_for_benefits", period) > 0
        )
        return benunit.sum(child * disabled)


class num_severely_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of severely disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        disabled = (
            benunit.members("is_severely_disabled_for_benefits", period) > 0
        )
        return benunit.sum(child * disabled)


class num_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of disabled adults"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        disabled = benunit.members("is_disabled_for_benefits", period) > 0
        return benunit.sum(adult * disabled)


class num_enhanced_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of enhanced disabled adults"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        disabled = (
            benunit.members("is_enhanced_disabled_for_benefits", period) > 0
        )
        return benunit.sum(adult * disabled)


class num_severely_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of severely disabled adults"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        disabled = (
            benunit.members("is_severely_disabled_for_benefits", period) > 0
        )
        return benunit.sum(adult * disabled)


class disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = u"Disability premium"
    definition_period = YEAR
    reference = "The Social Security Amendment (Enhanced Disability Premium) Regulations 2000"

    def formula(benunit, period, parameters):
        dis = parameters(period).benefit.disability_premia
        amount = (
            (benunit("num_disabled_adults", period.this_year) > 0)
            * (
                benunit("is_single", period.this_year) * dis.disability_single
                + benunit("is_couple", period.this_year)
                * dis.disability_couple
            )
            * WEEKS_IN_YEAR
        )
        return amount


class severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = u"Severe disability premium"
    definition_period = YEAR
    reference = "The Social Security Amendment (Enhanced Disability Premium) Regulations 2000"

    def formula(benunit, period, parameters):
        dis = parameters(period).benefit.disability_premia
        amount = (
            (benunit("num_severely_disabled_adults", period.this_year) > 0)
            * (
                benunit("is_single", period.this_year) * dis.severe_single
                + benunit("is_couple", period.this_year) * dis.severe_couple
            )
            * WEEKS_IN_YEAR
        )
        return amount


class enhanced_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = u"Enhanced disability premium"
    definition_period = YEAR
    reference = "The Social Security Amendment (Enhanced Disability Premium) Regulations 2000"

    def formula(benunit, period, parameters):
        dis = parameters(period).benefit.disability_premia
        amount = (
            (benunit("num_enhanced_disabled_adults", period.this_year) > 0)
            * (
                benunit("is_single", period.this_year) * dis.enhanced_single
                + benunit("is_couple", period.this_year) * dis.enhanced_couple
            )
            * WEEKS_IN_YEAR
        )
        return amount
