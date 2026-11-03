from policyengine_uk.model_api import *


class soc2020_major_group(Variable):
    value_type = int
    entity = Person
    label = "Standard Occupational Classification (2020) major group of the main or last job"
    documentation = (
        "SOC 2020 major group of the person's main job, or of their last job "
        "if they are not in work (0 if none or unknown). Sourced from the FRS "
        "`SOC2020` field, which codes the major group in thousands; the FRS "
        "asks the employment questions of everyone who has ever worked, so "
        "use employment_status to select current occupations. 1 = Managers, "
        "directors and senior officials; 2 = Professional occupations; "
        "3 = Associate professional occupations; 4 = Administrative and "
        "secretarial occupations; 5 = Skilled trades occupations; 6 = Caring, "
        "leisure and other service occupations; 7 = Sales and customer service "
        "occupations; 8 = Process, plant and machine operatives; "
        "9 = Elementary occupations."
    )
    default_value = 0
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
