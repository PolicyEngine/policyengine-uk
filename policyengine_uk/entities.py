# -*- coding: utf-8 -*-

# This file defines the entities needed by our legislation.
from policyengine_core.entities import build_entity

Household = build_entity(
    key="household",
    plural="households",
    label="Household",
    doc="Each household may contain multiple families, or benefit units.",
    roles=[
        {
            "key": "member",
            "plural": "members",
            "label": "Member",
            "doc": "A person who is a citizen of a country.",
        }
    ],
    containing_entities=["state"],
)

BenUnit = build_entity(
    key="benunit",
    plural="benunits",
    label="Benefit unit",
    doc="A family is also known as a benefit unit, and contains parents and dependent children.",
    roles=[
        {
            "key": "member",
            "plural": "members",
            "label": "Member",
            "doc": "A person who is a citizen of a country.",
        }
    ],
    containing_entities=["household", "state"],
)

Person = build_entity(
    key="person",
    plural="people",
    label="Person",
    doc="An individual. The minimal legal entity on which a legislation might be applied.",
    is_person=True,
)

# A firm is a root entity: a population of its own, with its own count, ids,
# weight and dataset table, and no members. People are not members of firms.
# policyengine-core has no root entity type, so Firm is a plain ``Entity``
# (``is_person`` is True, as for every non-group entity). Core takes the
# first ``is_person`` entity in the system's list as its person entity and
# makes the rest of the non-person entities its group entities, so Firm must
# come after Person in ``CountryTaxBenefitSystem``'s entity list: it is then
# neither the person entity nor a group entity, and
# ``CountryTaxBenefitSystem.instantiate_entities`` adds its population.
Firm = build_entity(
    key="firm",
    plural="firms",
    label="Firm",
    doc=(
        "A business: a company, sole trader or partnership. Firms form a "
        "population of their own, with no members. A simulation built from a "
        "household situation or dataset without firms has no firms."
    ),
    is_person=True,
)

entities = [Household, BenUnit, Person, Firm]
