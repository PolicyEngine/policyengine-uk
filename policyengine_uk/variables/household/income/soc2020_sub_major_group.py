from policyengine_uk.model_api import *


class soc2020_sub_major_group(Variable):
    value_type = int
    entity = Person
    label = "Standard Occupational Classification (2020) sub-major group of the main or last job"
    documentation = (
        "SOC 2020 sub-major group (a two-digit code) of the person's main job, "
        "or of their last job if they are not in work (0 if none or unknown). "
        "Its first digit is the major group in soc2020_major_group. The FRS "
        "end-user edition codes only the major group, so a dataset built on it "
        "has to impute the sub-major group within the major group from a "
        "survey that codes it, such as the Labour Force Survey or the Annual "
        "Population Survey. 11 = Corporate managers and directors; 12 = Other "
        "managers and proprietors; 21 = Science, research, engineering and "
        "technology professionals; 22 = Health professionals; 23 = Teaching "
        "and other educational professionals; 24 = Business, media and public "
        "service professionals; 31 = Science, engineering and technology "
        "associate professionals; 32 = Health and social care associate "
        "professionals; 33 = Protective service occupations; 34 = Culture, "
        "media and sports occupations; 35 = Business and public service "
        "associate professionals; 41 = Administrative occupations; "
        "42 = Secretarial and related occupations; 51 = Skilled agricultural "
        "and related trades; 52 = Skilled metal, electrical and electronic "
        "trades; 53 = Skilled construction and building trades; 54 = Textiles, "
        "printing and other skilled trades; 61 = Caring personal service "
        "occupations; 62 = Leisure, travel and related personal service "
        "occupations; 63 = Community and civil enforcement occupations; "
        "71 = Sales occupations; 72 = Customer service occupations; 81 = Process, "
        "plant and machine operatives; 82 = Transport and mobile machine "
        "drivers and operatives; 91 = Elementary trades and related "
        "occupations; 92 = Elementary administration and service occupations."
    )
    default_value = 0
    definition_period = YEAR
    reference = [
        dict(
            title="ONS, SOC 2020 Volume 1: structure and descriptions of unit groups",
            href="https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume1structureanddescriptionsofunitgroups",
        ),
    ]
