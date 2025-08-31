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

Firm = build_entity(
    key="firm",
    plural="firms",
    label="Firm",
    doc="A business entity with employees and operations.",
    is_person=True,
)

Sector = build_entity(
    key="sector",
    plural="sectors",
    label="Sector",
    doc="An economic sector containing multiple firms.",
    roles=[
        {
            "key": "member",
            "plural": "members",
            "label": "Member",
            "doc": "A sector in the business classification.",
        }
    ],
)

BusinessGroup = build_entity(
    key="business_group",
    plural="business_groups",
    label="Business Group",
    doc="A business group containing multiple firms.",
    roles=[
        {
            "key": "member",
            "plural": "members",
            "label": "Member",
            "doc": "A business group in the firm dataset.",
        }
    ],
)

entities = [Household, BenUnit, Person, Firm, Sector, BusinessGroup]
