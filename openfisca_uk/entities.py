# -*- coding: utf-8 -*-

# This file defines the entities needed by our legislation.
from openfisca_core.entities import build_entity

Household = build_entity(
    key = "household",
    plural = "households",
    label = u'All the people in a family or group who live together in the same place.',
    doc = u'Each household may contain multiple families, or benefit units.',
    roles = [
        {
            'key': 'family',
            'plural': 'families',
            'label': u'family',
            'doc': u'A family, or benefit unit, of a household.'
            }
        ]
    )

Family = build_entity(
    key = "family",
    plural = "families",
    label = u'A benefit unit, comprising of exactly one or two adults, plus any dependent children',
    doc = u'A family is also known as a benefit unit, and contains parents and dependent children.',
    roles = [
        {
            'key': 'parent',
            'plural': 'parents',
            'label': u'Parents',
            'max': 2,
            'subroles': ['first_parent', 'second_parent'],
            'doc': u'The one or two adults in the benefit unit.'
            },
        {
            'key': 'child',
            'plural': 'children',
            'label': u'Child',
            'doc': u'Dependent children.'
            }
        ]
    )

Person = build_entity(
    key = "person",
    plural = "persons",
    label = u'An individual. The minimal legal entity on which a legislation might be applied.',
    is_person = True,
    )

entities = [Household, Family, Person]