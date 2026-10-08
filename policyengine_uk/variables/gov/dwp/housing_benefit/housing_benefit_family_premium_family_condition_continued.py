from policyengine_uk.model_api import *


class housing_benefit_family_premium_family_condition_continued(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit family premium family condition continued"
    documentation = "Since the applicable family-premium abolition date, the claimant's family has continuously included a child or young person; changing which child qualifies does not itself end protection."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )
