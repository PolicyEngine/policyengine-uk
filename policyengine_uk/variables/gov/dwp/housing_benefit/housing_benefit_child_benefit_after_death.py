from policyengine_uk.model_api import *


class housing_benefit_child_benefit_after_death(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit child benefit after death"
    documentation = "Claimant or partner remains entitled to Child Benefit in respect of this child/young person after death under section 145A, within its prescribed period."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )
