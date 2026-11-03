from policyengine_uk.model_api import *


class SOC2020MajorGroup(Enum):
    NONE = "No occupation recorded"
    MANAGERS_DIRECTORS_AND_SENIOR_OFFICIALS = "Managers, directors and senior officials"
    PROFESSIONAL = "Professional occupations"
    ASSOCIATE_PROFESSIONAL = "Associate professional occupations"
    ADMINISTRATIVE_AND_SECRETARIAL = "Administrative and secretarial occupations"
    SKILLED_TRADES = "Skilled trades occupations"
    CARING_LEISURE_AND_OTHER_SERVICE = "Caring, leisure and other service occupations"
    SALES_AND_CUSTOMER_SERVICE = "Sales and customer service occupations"
    PROCESS_PLANT_AND_MACHINE_OPERATIVES = "Process, plant and machine operatives"
    ELEMENTARY = "Elementary occupations"


class soc2020_major_group(Variable):
    value_type = Enum
    possible_values = SOC2020MajorGroup
    default_value = SOC2020MajorGroup.NONE
    entity = Person
    label = "Standard Occupational Classification (2020) major group of the main or last job"
    documentation = (
        "SOC 2020 major group of the person's main job, or of their last job "
        "if they are not in work; NONE if there is none or it is unknown. "
        "Sourced from the FRS `SOC2020` field, which codes major groups 1 to "
        "9 as 1000 to 9000; the FRS asks the employment questions of everyone "
        "who has ever worked, so use employment_status to select current "
        "occupations. After NONE, the members follow the SOC 2020 codes in "
        "order, 1 to 9."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="ONS, SOC 2020 Volume 1: structure and descriptions of unit groups",
            href="https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume1structureanddescriptionsofunitgroups",
        ),
        dict(
            title="DWP, Family Resources Survey 2024-25 question instructions (employment details, p. 184)",
            href="https://doc.ukdataservice.ac.uk/doc/9563/mrdoc/pdf/9563_frs_2024-25_question_instructions_final.pdf",
        ),
    ]
