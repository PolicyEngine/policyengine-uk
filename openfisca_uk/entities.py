# -*- coding: utf-8 -*-

# This file defines the entities needed by our legislation.
from openfisca_core.entities import build_entity

Household = build_entity(
    key="household",
    plural="households",
    label=u"Household",
    doc=u"Each household may contain multiple families, or benefit units.",
    roles=[
        {
            "key": "adult",
            "plural": "adults",
            "label": u"Adult",
            "doc": u"The adults in the household.",
        },
        {
            "key": "child",
            "plural": "children",
            "label": u"Child",
            "doc": u"Dependent children in the household.",
        },
    ],
)

BenUnit = build_entity(
    key="benunit",
    plural="benunits",
    label=u"Benefit unit",
    doc=u"A family is also known as a benefit unit, and contains parents and dependent children.",
    roles=[
        {
            "key": "adult",
            "plural": "adults",
            "label": u"Adult",
            "max": 2,
            "doc": u"The one or two adults in the benefit unit.",
        },
        {
            "key": "child",
            "plural": "children",
            "label": u"Child",
            "doc": u"Dependent children.",
        },
    ],
)

Person = build_entity(
    key="person",
    plural="people",
    label="Person",
    doc=u"An individual. The minimal legal entity on which a legislation might be applied.",
    is_person=True,
)

entities = [Household, BenUnit, Person]
