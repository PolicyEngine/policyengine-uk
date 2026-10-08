from policyengine_uk.model_api import *


class permitted_work_authority_approved(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "permitted work authority approved"
    documentation = "The competent authority has accepted that this person is undertaking work of a prescribed exempt-work kind. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
