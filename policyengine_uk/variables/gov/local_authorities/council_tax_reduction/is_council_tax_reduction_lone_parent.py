from policyengine_uk.model_api import *


class is_council_tax_reduction_lone_parent(Variable):
    value_type = bool
    entity = BenUnit
    label = "Lone parent for Council Tax Reduction"
    documentation = (
        "A person who has no partner and who is responsible for and a member "
        "of the same household as a child or young person, under the young "
        "person definition of the Council Tax Reduction scheme that applies "
        "to the family: the Universal Credit qualifying young person in "
        "Scotland's working-age scheme from 1 April 2022, and the Child "
        "Benefit qualifying young person elsewhere."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/4",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/2",
    )

    def formula(benunit, period, parameters):
        return benunit("is_single", period) & benunit(
            "is_responsible_for_child_or_young_person_for_council_tax_reduction",
            period,
        )
