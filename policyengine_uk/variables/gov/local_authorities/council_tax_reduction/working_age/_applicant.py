from policyengine_uk.model_api import *


def working_age_applicant_or_partner(person, period):
    """The people whose circumstances the working-age assessment counts.

    Scotland and Wales assess the applicant and partner (SSI 2021/249 reg 36;
    WSI 2013/3029 Sch 6 para 7). Every working-age CTR variable reads its
    person mask from here, so a change to who the applicant is needs one edit.
    """
    return person("is_claimant_or_partner", period)
