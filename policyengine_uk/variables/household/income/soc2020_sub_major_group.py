from policyengine_uk.model_api import *


class SOC2020SubMajorGroup(Enum):
    NONE = "No occupation recorded"
    CORPORATE_MANAGERS_AND_DIRECTORS = "Corporate managers and directors"
    OTHER_MANAGERS_AND_PROPRIETORS = "Other managers and proprietors"
    SCIENCE_RESEARCH_ENGINEERING_AND_TECHNOLOGY_PROFESSIONALS = (
        "Science, research, engineering and technology professionals"
    )
    HEALTH_PROFESSIONALS = "Health professionals"
    TEACHING_AND_OTHER_EDUCATIONAL_PROFESSIONALS = (
        "Teaching and other educational professionals"
    )
    BUSINESS_MEDIA_AND_PUBLIC_SERVICE_PROFESSIONALS = (
        "Business, media and public service professionals"
    )
    SCIENCE_ENGINEERING_AND_TECHNOLOGY_ASSOCIATE_PROFESSIONALS = (
        "Science, engineering and technology associate professionals"
    )
    HEALTH_AND_SOCIAL_CARE_ASSOCIATE_PROFESSIONALS = (
        "Health and social care associate professionals"
    )
    PROTECTIVE_SERVICE = "Protective service occupations"
    CULTURE_MEDIA_AND_SPORTS = "Culture, media and sports occupations"
    BUSINESS_AND_PUBLIC_SERVICE_ASSOCIATE_PROFESSIONALS = (
        "Business and public service associate professionals"
    )
    ADMINISTRATIVE = "Administrative occupations"
    SECRETARIAL_AND_RELATED = "Secretarial and related occupations"
    SKILLED_AGRICULTURAL_AND_RELATED_TRADES = "Skilled agricultural and related trades"
    SKILLED_METAL_ELECTRICAL_AND_ELECTRONIC_TRADES = (
        "Skilled metal, electrical and electronic trades"
    )
    SKILLED_CONSTRUCTION_AND_BUILDING_TRADES = (
        "Skilled construction and building trades"
    )
    TEXTILES_PRINTING_AND_OTHER_SKILLED_TRADES = (
        "Textiles, printing and other skilled trades"
    )
    CARING_PERSONAL_SERVICE = "Caring personal service occupations"
    LEISURE_TRAVEL_AND_RELATED_PERSONAL_SERVICE = (
        "Leisure, travel and related personal service occupations"
    )
    COMMUNITY_AND_CIVIL_ENFORCEMENT = "Community and civil enforcement occupations"
    SALES = "Sales occupations"
    CUSTOMER_SERVICE = "Customer service occupations"
    PROCESS_PLANT_AND_MACHINE_OPERATIVES = "Process, plant and machine operatives"
    TRANSPORT_AND_MOBILE_MACHINE_DRIVERS_AND_OPERATIVES = (
        "Transport and mobile machine drivers and operatives"
    )
    ELEMENTARY_TRADES_AND_RELATED = "Elementary trades and related occupations"
    ELEMENTARY_ADMINISTRATION_AND_SERVICE = (
        "Elementary administration and service occupations"
    )


# The two-digit SOC 2020 code of each sub-major group, by member name, so that
# datasets and crosswalks keyed on codes need not rely on member order. A
# code's first digit is its major group's code. NONE has no code.
SOC2020_SUB_MAJOR_GROUP_CODES = {
    "CORPORATE_MANAGERS_AND_DIRECTORS": 11,
    "OTHER_MANAGERS_AND_PROPRIETORS": 12,
    "SCIENCE_RESEARCH_ENGINEERING_AND_TECHNOLOGY_PROFESSIONALS": 21,
    "HEALTH_PROFESSIONALS": 22,
    "TEACHING_AND_OTHER_EDUCATIONAL_PROFESSIONALS": 23,
    "BUSINESS_MEDIA_AND_PUBLIC_SERVICE_PROFESSIONALS": 24,
    "SCIENCE_ENGINEERING_AND_TECHNOLOGY_ASSOCIATE_PROFESSIONALS": 31,
    "HEALTH_AND_SOCIAL_CARE_ASSOCIATE_PROFESSIONALS": 32,
    "PROTECTIVE_SERVICE": 33,
    "CULTURE_MEDIA_AND_SPORTS": 34,
    "BUSINESS_AND_PUBLIC_SERVICE_ASSOCIATE_PROFESSIONALS": 35,
    "ADMINISTRATIVE": 41,
    "SECRETARIAL_AND_RELATED": 42,
    "SKILLED_AGRICULTURAL_AND_RELATED_TRADES": 51,
    "SKILLED_METAL_ELECTRICAL_AND_ELECTRONIC_TRADES": 52,
    "SKILLED_CONSTRUCTION_AND_BUILDING_TRADES": 53,
    "TEXTILES_PRINTING_AND_OTHER_SKILLED_TRADES": 54,
    "CARING_PERSONAL_SERVICE": 61,
    "LEISURE_TRAVEL_AND_RELATED_PERSONAL_SERVICE": 62,
    "COMMUNITY_AND_CIVIL_ENFORCEMENT": 63,
    "SALES": 71,
    "CUSTOMER_SERVICE": 72,
    "PROCESS_PLANT_AND_MACHINE_OPERATIVES": 81,
    "TRANSPORT_AND_MOBILE_MACHINE_DRIVERS_AND_OPERATIVES": 82,
    "ELEMENTARY_TRADES_AND_RELATED": 91,
    "ELEMENTARY_ADMINISTRATION_AND_SERVICE": 92,
}


class soc2020_sub_major_group(Variable):
    value_type = Enum
    possible_values = SOC2020SubMajorGroup
    default_value = SOC2020SubMajorGroup.NONE
    entity = Person
    label = "Standard Occupational Classification (2020) sub-major group of the main or last job"
    documentation = (
        "SOC 2020 sub-major group of the person's main job, or of their last "
        "job if they are not in work; NONE if there is none or it is unknown. "
        "Each sub-major group lies within one major group "
        "(soc2020_major_group). The FRS end-user edition codes only the major "
        "group, so a dataset built on it has to impute the sub-major group "
        "within the major group from a survey that codes it, such as the "
        "Labour Force Survey or the Annual Population Survey. "
        "SOC2020_SUB_MAJOR_GROUP_CODES, in this module, gives each member's "
        "two-digit SOC 2020 code, whose first digit is its major group's code."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="ONS, SOC 2020 Volume 1: structure and descriptions of unit groups",
            href="https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume1structureanddescriptionsofunitgroups",
        ),
    ]
