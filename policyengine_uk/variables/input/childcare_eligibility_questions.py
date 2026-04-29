from policyengine_uk.model_api import *


class is_about_to_start_paid_work(Variable):
    value_type = bool
    entity = Person
    label = "about to start paid work"
    documentation = (
        "Whether this person is about to start paid work. Some childcare "
        "support programs (e.g. Tax-Free Childcare under SI 2015/448) treat "
        "imminent starters as in qualifying paid work for eligibility "
        "purposes. Captured as an input so front-ends can prompt users and "
        "future program formulas can consume it."
    )
    definition_period = YEAR
    default_value = False


class is_newly_self_employed(Variable):
    value_type = bool
    entity = Person
    label = "newly self-employed (business under 12 months old)"
    documentation = (
        "Whether this person has been self-employed for less than 12 "
        "months. Several childcare support programs relax income or work "
        "tests during a self-employment start-up period. For Tax-Free "
        "Childcare specifically, the more narrowly-scoped "
        "`tax_free_childcare_self_employment_start_up_period` input is "
        "what the eligibility formula consumes; this variable exists as a "
        "general-purpose question for front-ends covering multiple "
        "childcare programs."
    )
    definition_period = YEAR
    default_value = False
