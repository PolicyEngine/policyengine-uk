from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_childcare_disabled_partner(Variable):
    value_type = bool
    entity = Person
    label = "Plymouth Council Tax Support source-defined disabled partner for childcare deduction"
    documentation = "Covers source incapacity and disability statuses for partner childcare eligibility not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = False
