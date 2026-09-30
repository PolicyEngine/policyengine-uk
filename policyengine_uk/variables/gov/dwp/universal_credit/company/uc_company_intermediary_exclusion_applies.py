from policyengine_uk.model_api import *


class uc_company_intermediary_exclusion_applies(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit company owner rule excluded by the intermediaries rules"
    documentation = (
        "Whether income the person derives from the company is employed "
        "earnings under the intermediaries or managed service company rules "
        "in a way that takes them out of Universal Credit's company owner "
        "rule: Chapter 8 or 9 of Part 2 of ITEPA 2003 until 27 November 2018; "
        "Chapter 8, 9 or 10, derived from activities that are the person's "
        "main employment, from 28 November 2018."
    )
    definition_period = YEAR
    reference = dict(
        title="The Universal Credit Regulations 2013 reg. 77(5)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
    )

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dwp.universal_credit.company_owner.intermediary_exclusion
        chapter = person("owned_company_intermediary_earnings_chapter", period)
        excluded_chapter = np.isin(chapter.decode_to_str(), p.chapters)
        from_main_employment = person(
            "owned_company_intermediary_earnings_from_main_employment", period
        )
        return excluded_chapter & (from_main_employment | ~p.requires_main_employment)
