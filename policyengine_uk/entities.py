# -*- coding: utf-8 -*-

# This file defines the entities needed by our legislation.
from policyengine_core.entities import build_entity

State = build_entity(
    key="state",
    plural="states",
    label="State",
    roles=[
        {
            "key": "member",
            "plural": "members",
            "label": "Member",
            "doc": "A person who is a citizen of a country.",
        }
    ],
)

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

entities = [State, Household, BenUnit, Person]
