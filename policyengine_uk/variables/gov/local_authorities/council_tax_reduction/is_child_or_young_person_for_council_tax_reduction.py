from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class is_child_or_young_person_for_council_tax_reduction(Variable):
    """Child or young person in the applicant's family for Council Tax Reduction.

    Every scheme defines a child as a person under 16. Scotland's working-age
    scheme from 1 April 2022 uses the Universal Credit child and qualifying
    young person tests (SSI 2021/249 regs. 4 and 6), with its own looked-after
    placement rule in reg. 7. The qualifying young person test retains the
    model's reading of UC reg. 5 as including SI 2014/1230 reg. 28(b)'s
    existing-benefit modification under Interpretation Act 1978 ss. 20(2) and
    23(1). Whether the Scottish reference carries that modification remains
    unsettled; this variable leaves the existing interpretation unchanged.

    Until 30 October 2024, reg. 7(8) excludes a looked-after child unless placed
    with, or living with, a parent, a person with parental responsibility or
    an approved kinship carer. From 31 October 2024, SSI 2024/230 excludes only
    a child placed with a foster carer under the Looked After Children
    (Scotland) Regulations 2009. The applicant's normal responsibility and the
    existing claimant-or-partner screen still apply.

    scottish_council_tax_reduction_child_placement refines only an existing
    is_looked_after_child flag. Foster, approved kinship and other looked-after
    arrangements require the existing looked-after input to be true. Parent
    or parental-responsibility placements keep that input false under its
    Universal Credit exception convention. The new input never changes
    Universal Credit or the global looked-after flags. UNSPECIFIED keeps the
    existing exclusion for a flagged child as a compatibility fallback; it
    does not establish that an unknown arrangement is a foster placement.

    The dated rule follows the model's ordinary government-parameter
    conversion, which samples 30 April for each annual label. Annual 2024
    therefore retains the earlier rule and annual 2025 uses the amended rule;
    there is no within-year split of the annual child flag.

    England, Wales, Scotland's pension-age scheme and Scotland's working-age
    scheme before 1 April 2022 retain the Child Benefit qualifying-young-person
    and legacy household tests. That branch excludes looked-after children and
    children placed for adoption. The Scottish working-age branch from April
    2022 retains children placed for adoption, as the Universal Credit child
    tests do, while applying Scotland's own looked-after placement rule.
    """

    value_type = bool
    entity = Person
    label = "Child or young person for Council Tax Reduction"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/ukpga/1978/30/section/20",
        "https://www.legislation.gov.uk/ukpga/1978/30/section/23",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/6",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/7",
        "https://www.legislation.gov.uk/ssi/2024/230/made",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/4",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/2",
    )

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.working_age
        scottish_working_age = (
            (person.household("country", period) == Country.SCOTLAND)
            & ~person.benunit("council_tax_reduction_pensioner", period)
            & p.young_person_follows_universal_credit
        )
        # Reuse the UC age and qualifying-young-person tests, applying
        # Scotland's reg. 7 placement exclusion in place of UC reg. 4(6)(a).
        child_or_young_person = person(
            "is_child_for_universal_credit", period
        ) | person("is_qualifying_young_person_for_universal_credit", period)
        placement = person("scottish_council_tax_reduction_child_placement", period)
        placement_types = placement.possible_values
        earlier_exception = (placement == placement_types.APPROVED_KINSHIP_CARER) | (
            placement == placement_types.PARENT_OR_PARENTAL_RESPONSIBILITY
        )
        foster_or_unspecified = (placement == placement_types.FOSTER_CARER) | (
            placement == placement_types.UNSPECIFIED
        )
        excluded_placement = where(
            p.looked_after_exclusion_is_foster_only,
            foster_or_unspecified,
            ~earlier_exception,
        )
        scottish_child = (
            child_or_young_person
            & ~person("is_claimant_or_partner", period)
            & ~(person("is_looked_after_child", period) & excluded_placement)
        )
        child_benefit = person("is_child_or_young_person_for_legacy_benefits", period)
        return where(scottish_working_age, scottish_child, child_benefit)
