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
        "Labour Force Survey or the Annual Population Survey. After NONE, the "
        "members follow the SOC 2020 codes in order: 11, 12, 21, 22, 23, 24, "
        "31, 32, 33, 34, 35, 41, 42, 51, 52, 53, 54, 61, 62, 63, 71, 72, 81, "
        "82, 91 and 92."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="ONS, SOC 2020 Volume 1: structure and descriptions of unit groups",
            href="https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume1structureanddescriptionsofunitgroups",
        ),
    ]
