from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class is_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether claims a core disability benefit"
    definition_period = YEAR

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "ESA_contrib",
            "incapacity_benefit",
            "SDA",
            "AA",
            "DLA_M",
            "DLA_SC",
        ]
        return add(person, period, QUALIFYING_BENEFITS, options=[MATCH]) > 0


class is_severely_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether is eligible for higher payments of disability benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        claiming_SDA = person("SDA", period, options=[MATCH]) > 0
        no_non_dependents = person.benunit.nb_persons(BenUnit.ADULT) == 1
        sufficient_DLA = person("DLA_SC", period, options=[MATCH]) > 50
        return (claiming_SDA + sufficient_DLA > 0) * no_non_dependents


class is_enhanced_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether meets the highest disability benefit entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        sufficient_DLA = person("DLA_SC", period, options=[MATCH]) > 80
        return sufficient_DLA


class is_carer(Variable):
    value_type = bool
    entity = Person
    label = u"Whether meets eligibility requirements for Carers Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        already_claiming = (
            person("carers_allowance", period, options=[MATCH]) > 0
        )
        meets_requirements = (
            person("care_hours", period)
            >= parameters(period).benefits.carers_allowance.min_hours
        )
        return already_claiming + meets_requirements


class registered_disabled(Variable):
    value_type = bool
    entity = Person
    label = u"Whether registered disabled"
    definition_period = YEAR


class dis_equality_act_core(Variable):
    value_type = bool
    entity = Person
    label = u"Whether disabled under the Equality Act (core definition)"
    definition_period = YEAR


class dis_equality_act_wider(Variable):
    value_type = bool
    entity = Person
    label = u"Whether disabled under the Equality Act (wider definition)"
    definition_period = YEAR


class is_standard_disabled(Variable):
    value_type = bool
    entity = Person
    label = u"Whether meets a basic level of disability"
    definition_period = YEAR

    def formula(person, period, parameters):
        QUALIFYING = [
            "is_disabled",
            "is_severely_disabled",
            "is_enhanced_disabled",
            "IIDB",
            "registered_disabled",
            "dis_equality_act_core",
        ]
        return add(person, period, QUALIFYING, options=[MATCH])


class is_disabled_for_ubi(Variable):
    value_type = float
    entity = Person
    label = u"Whether person is classified as disabled for the purposes of UBI supplements"
    definition_period = YEAR

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "ESA_contrib",
            "incapacity_benefit",
            "SDA",
            "AA",
            "DLA_M",
            "DLA_SC",
            "IIDB",
            # Given to a single person at benunit level
            "PIP_DL",
            "PIP_M",
            "ESA_income",
        ]
        return add(person, period, QUALIFYING_BENEFITS, options=[MATCH]) > 0


class is_severely_disabled_for_ubi(Variable):
    value_type = float
    entity = Person
    label = u"Whether person is classified as severely disabled for the purposes of UBI supplements"
    definition_period = YEAR

    def formula(person, period, parameters):
        def compare(ben: str, value: float, factor: float):
            """Check if a benefit exceeds a value.

            :param ben: Benefit name.
            :type ben: str
            :param value: Comparison value, e.g. parameter value.
            :type value: float
            :param factor: Multiplication factor, e.g. to give a buffer.
            :type factor: float
            :return: Series of bools.
            :rtype: pandas Series
            """
            return person(ben, period, options=[MATCH]) > value * factor

        # First check if person gets at least middle amount of DLA_SC
        DLA_care_middle = compare(
            "DLA_SC", parameters(period).benefits.DLA.care_middle, 0.8
        )
        DLA_mobility_upper = compare(
            "DLA_M", parameters(period).benefits.DLA.mobility_upper, 0.8
        )
        IIDB_40p = compare(
            "IIDB", parameters(period).benefits.IIDB.maximum, 0.4
        )
        PIP_DL_severe = compare(
            "PIP_DL", parameters(period).benefits.PIP.severe_daily_living, 0.8
        )
        PIP_M_severe = compare(
            "PIP_M", parameters(period).benefits.PIP.severe_mobility, 0.8
        )
        AA_lower = compare(
            "AA", parameters(period).benefits.attendance_allowance.lower, 0.8
        )
        claiming_SDA = person("SDA", period, options=[MATCH]) > 0
        return (
            DLA_care_middle
            + DLA_mobility_upper
            + IIDB_40p
            + PIP_DL_severe
            + PIP_M_severe
            + AA_lower
            + claiming_SDA
        ) > 0


class is_enhanced_disabled_for_ubi(Variable):
    value_type = float
    entity = Person
    label = u"Whether person is classified as enhanced disabled for the purposes of UBI supplements"
    definition_period = YEAR

    def formula(person, period, parameters):
        def compare(ben: str, value: float, factor: float):
            """Check if a benefit exceeds a value.

            :param ben: Benefit name.
            :type ben: str
            :param value: Comparison value, e.g. parameter value.
            :type value: float
            :param factor: Multiplication factor, e.g. to give a buffer.
            :type factor: float
            :return: Series of bools.
            :rtype: pandas Series
            """
            return person(ben, period, options=[MATCH]) > value * factor

        # First check if person gets at least middle amount of DLA_SC
        DLA_care_highest = compare(
            "DLA_SC", parameters(period).benefits.DLA.care_highest, 0.8
        )
        IIDB_80p = compare(
            "IIDB", parameters(period).benefits.IIDB.maximum, 0.8
        )
        AA_upper = compare(
            "AA", parameters(period).benefits.attendance_allowance.upper, 0.8
        )
        return (DLA_care_highest + IIDB_80p + AA_upper) > 0
