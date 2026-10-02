"""Benefit-unit composition for the labour supply elasticity groups.

The OBR labour supply note (Tables A1 and A2) assigns elasticities by
partnership and by the presence and age of the youngest child, without
defining a child. The dynamics modules keep an explicit age band for this:
benefit-unit members under 18 are children and members aged 18 or over are
adults. This is a modelling choice for the elasticity groups, not a legal
definition.

Reference: https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf
"""

import numpy as np
import pandas as pd


def benunit_age_18_composition(sim) -> pd.DataFrame:
    """Per-person view of their benefit unit, split at age 18.

    Returns a DataFrame aligned with the person entity, with columns:
    - count_under_18: benefit-unit members under 18;
    - youngest_under_18_age: age of the youngest such member (inf if none);
    - count_aged_18_or_over: benefit-unit members aged 18 or over.
    """
    age = np.asarray(sim.calculate("age"), dtype=float)
    # Position of each person's benefit unit, from the simulation's own entity
    # structure (works for datasets and hand-built situations alike).
    benunit_id = np.asarray(sim.populations["benunit"].members_entity_id)
    under_18 = age < 18
    people = pd.DataFrame(
        {
            "benunit_id": benunit_id,
            "under_18": under_18,
            "aged_18_or_over": ~under_18,
            "age_if_under_18": np.where(under_18, age, np.inf),
        }
    )
    by_benunit = people.groupby("benunit_id").agg(
        count_under_18=("under_18", "sum"),
        youngest_under_18_age=("age_if_under_18", "min"),
        count_aged_18_or_over=("aged_18_or_over", "sum"),
    )
    return by_benunit.reindex(benunit_id).reset_index(drop=True)
