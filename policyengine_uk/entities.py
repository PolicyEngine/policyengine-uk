# -*- coding: utf-8 -*-

# This file defines the entities needed by our legislation.
from openfisca_core.entities import build_entity

State = build_entity(
    key="state",
    plural="states",
    label="State",
    roles=[
        {
            "key": "citizen",
            "plural": "citizens",
            "label": "Citizen",
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
            "key": "adult",
            "plural": "adults",
            "label": "Adult",
            "doc": "The adults in the household.",
        },
        {
            "key": "child",
            "plural": "children",
            "label": "Child",
            "doc": "Dependent children in the household.",
        },
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
            "key": "adult",
            "plural": "adults",
            "label": "Adult",
            "max": 2,
            "doc": "The one or two adults in the benefit unit.",
        },
        {
            "key": "child",
            "plural": "children",
            "label": "Child",
            "doc": "Dependent children.",
        },
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
