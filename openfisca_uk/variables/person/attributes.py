from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

# Input from FRS


class person_id(Variable):
    value_type = int
    entity = Person
    label = u"ID of the person"
    definition_period = ETERNITY


class age(Variable):
    value_type = float
    entity = Person
    label = u"Age in years"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period


class is_adult(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is an adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) >= 18


class is_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is a child"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 18


class is_benunit_head(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the head of the benefit unit"
    definition_period = ETERNITY


class is_household_head(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the head of the household"
    definition_period = ETERNITY


class hours(Variable):
    value_type = float
    entity = Person
    label = u"Hours worked per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period


class care_hours_given(Variable):
    value_type = float
    entity = Person
    label = u"Hours spent per week providing care"
    definition_period = WEEK


class care_hours_recieved(Variable):
    value_type = float
    entity = Person
    label = u"Hours spent per week providing care"
    definition_period = WEEK


class adult_weight(Variable):
    value_type = float
    entity = Person
    label = u"Weight of the adult"
    definition_period = ETERNITY


class is_married(Variable):
    value_type = float
    entity = Person
    label = u"Whether is married"
    definition_period = YEAR

class is_employee(Variable):
    value_type = float
    entity = Person
    label = u'Whether is an employee'
    definition_period = YEAR

class is_self_employed(Variable):
    value_type = float
    entity = Person
    label = u'Whether is self-employed'
    definition_period = YEAR


# Derived variables


class weekly_hours(Variable):
    value_type = float
    entity = Person
    label = u"Average weekly hours for the year"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("hours", period, options=[ADD]) / 52


class is_young_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is under 14"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 14


class is_older_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over 14 but under 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period.this_year) >= 14) * (
            person("age", period.this_year) < 18
        )


class is_SP_age(Variable):
    value_type = bool
    entity = Person
    label = u"Whether over the State Pension Age"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return (person("age", period.this_year) >= 65) + (
            person("state_pension", period) > 0
        )


class is_WA_adult(Variable):
    value_type = bool
    entity = Person
    label = u"Whether is a working-age adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_adult", period) * not_(person("is_SP_age", period))

class Age_group(Enum):
    child = u"child"
    WA_adult = u"WA adult"
    pensioner = u"pensioner"


class age_group(Variable):
    value_type = Enum
    possible_values = Age_group
    default_value = Age_group.WA_adult
    entity = Person
    label = u'Whether a child, adult or pensioner'
    definition_period = YEAR

    def formula(person, period, parameters):
        return select([person("is_child", period), person("is_WA_adult", period), person("is_SP_age", period)], [Age_group.child, Age_group.WA_adult, Age_group.pensioner])


class living_in_social_housing(Variable):
    value_type = bool
    entity = Person
    label = u"Whether is living in social housing"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person.household("is_social", period)


class living_in_shared_accomodation(Variable):
    value_type = bool
    entity = Person
    label = u"Whether is living in social housing"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person.household("is_shared", period)


class person_region(Variable):
    value_type = int
    entity = Person
    label = u"This person's region"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person.household("region", period)


class is_renting(Variable):
    value_type = float
    entity = Person
    label = u"Whether is renting"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.household("is_rented", period)


class num_bedrooms_in_household(Variable):
    value_type = float
    entity = Person
    label = u"The number of bedrooms in this person's household"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person.household("num_bedrooms", period)

class age_under_18(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is under age 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 18


class age_18_64(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is age 18 to 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period.this_year)
        return (age >= 18) & (age <= 64)


class age_over_64(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over age 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) > 64

# Enums

class Highest_qualification(Enum):
    unknown = u"unknown"
    doctorate = u"doctorate"
    postgraduate_degree = u"postgraduate_degree"
    degree = u"degree"
    teaching_qual = u"teaching_qual"
    foreign_degree_level = u"foreign_degree_level"
    work_degree_level = u"work_degree_level"
    other_prof_degree_level = u"other_prof_degree_level"
    HE_below_degree = u"HE_below_degree"
    nursing = u"nursing"
    diploma_in_HE = u"diploma_in_HE"
    HNC = u"HNC"
    BTEC_higher = u"BTEC_higher"
    SCOTVEC = u"SCOTVEC"
    NVQ_level_4 = u"NVQ_level_4"
    NVQ_level_5 = u"NVQ_level_5"
    OCT_level_4 = u"OCT_level_4"
    A_level = u"A_level"
    welsh_bacc_advanced = u"welsh_bacc_advanced"
    scot_bacc = u"scot_bacc"
    IB = u"IB"
    AS_level = u"AS_level"
    CSYS = u"CSYS"
    access_HE = u"access_HE"
    advanced_higher_qual = u"advanced_higher_qual"
    skills_for_work_higher = u"skills_for_work_higher"
    ONC = u"ONC"
    BTEC_Nat = u"BTEC_Nat"
    SCOTVEC_full = u"SCOTVEC_full"
    new_diploma_advanced = u"new_diploma_advanced"
    new_diploma_progression = u"new_diploma_progression"
    NVQ = u"NVQ"
    GNVQ = u"GNVQ"
    OCR_advanced = u"OCR_advanced"
    city_and_guilds = u"city_and_guilds"
    welsh_bacc_intermediate = u"welsh_bacc_intermediate"
    Five_O_levels = u"5_O_levels"
    Five_SG_scot = u"5_SG_scot"
    GCSE = u"GCSE"
    Five_CSEs = u"5_CSEs"
    scot_nat_level_5 = u"scot_nat_level_5"
    skills_for_work_level_5 = u"skills_for_work_level_5"
    BTEC_general_diploma = u"BTEC_general_diploma"
    SCOTVEC_general_diploma = u"SCOTVEC_general_diploma"
    new_diploma_higher = u"new_diploma_higher"
    NVQ_level_2 = u"NVQ_level_2"
    GNVQ_full_intermediate = u"GNVQ_full_intermediate"
    OCR_level_2 = u"OCR_level_2"
    city_and_guilds_part_2 = u"city_and_guilds_part_2"
    other_HS_leaver_qual = u"other_HS_leaver_qual"
    BTEC = u"BTEC"
    BTEC_general_cert = u"BTEC_general_cert"
    SCOTVEC_2 = u"SCOTVEC"
    SCOTVEC_general_cert = u"SCOTVEC_general_cert"
    SCOTVEC_nat_modules = u"SCOTVEC_nat_modules"
    new_diploma = u"new_diploma"
    new_diploma_foundation = u"new_diploma_foundation"
    welsh_bacc = u"welsh_bacc"
    welsh_bacc_foundation = u"welsh_bacc_foundation"
    NVQ_2 = u"NVQ"
    NVQ_level_1 = u"NVQ_level_1"
    GNVQ_2 = u"GNVQ"
    GNVQ_part_one = u"GNVQ_part_one"
    GNVQ_full_foundation = u"GNVQ_full_foundation"
    GNVQ_part_one_foundation = u"GNVQ_part_one_foundation"
    Five_O_levels_2 = u"5_O_levels"
    under_5_O_levels = u"under_5_O_levels"
    Five_SGs = u"5_SGs"
    under_5_SGs = u"under_5_SGs"
    Five_GCSEs = u"5_GCSEs"
    under_5_GCSEs = u"under_5_GCSEs"
    scot_nat_level_1 = u"scot_nat_level_1"
    scot_nat = u"scot_nat"
    skills_for_work_nat_level_3 = u"skills_for_work_nat_level_3"
    skills_for_work = u"skills_for_work"
    Five_CSEs_2 = u"5_CSEs"
    under_5_CSEs = u"under_5_CSEs"
    OCR = u"OCR"
    OCR_2 = u"OCR"
    city_and_guilds_2 = u"city_and_guilds"
    city_and_guilds_foundation = u"city_and_guilds_foundation"
    YTP = u"YTP"
    core_skills = u"core_skills"
    basic_skills = u"basic_skills"
    entry_level_qual = u"entry_level_qual"
    entry_level_award = u"entry_level_award"
    other_qual = u"other_qual"

class Education_type(Enum):
    unknown = u"unknown"
    school_full_time = u"school_full_time"
    school_part_time = u"school_part_time"
    sandwich_course = u"sandwich_course"
    uni_or_college = u"uni_or_college"
    training = u"training"
    uni_or_college_PT = u"uni_or_college_PT"
    open_college = u"open_college"
    open_university = u"open_university"
    other_correspondence_course = u"other_correspondence_course"
    other_course = u"other_course"

class Ethnicity(Enum):
    unknown = u"unknown"
    white = u"white"
    mixed = u"mixed"
    asian = u"asian"
    black = u"black"
    other = u"other"

class Ethicity_detailed(Enum):
    unknown = u"unknown"
    white_non_irish = u"white_non_irish"
    white_irish = u"white_irish"
    white_gypsy = u"white_gypsy"
    white_other = u"white_other"
    mixed_white_black_caribbean = u"mixed_white_black_caribbean"
    mixed_white_black_african = u"mixed_white_black_african"
    mixed_white_asian = u"mixed_white_asian"
    mixed_other = u"mixed_other"
    asian_indian = u"asian_indian"
    asian_pakistani = u"asian_pakistani"
    asian_bangladeshi = u"asian_bangladeshi"
    chinese = u"chinese"
    asian_other = u"asian_other"
    black_african = u"black_african"
    black_caribbean = u"black_caribbean"
    black_other = u"black_other"
    arab = u"arab"
    other = u"other"

class Marital_status(Enum):
    unknown = u"unknown"
    married = u"married"
    cohabiting = u"cohabiting"
    single = u"single"
    widowed = u"widowed"
    separated = u"separated"
    divorced = u"divorced"

class Standard_occ_class(Enum):
    unknown = u"unknown"
    managerial = u"managerial"
    professional = u"professional"
    techical = u"techical"
    admin = u"admin"
    skilled_trades = u"skilled_trades"
    care = u"care"
    sales = u"sales"
    manufacturing = u"manufacturing"
    elementary = u"elementary"
