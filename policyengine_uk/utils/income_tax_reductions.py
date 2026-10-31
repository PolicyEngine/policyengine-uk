"""Step 6 of the Income Tax calculation (ITA 2007 s. 23): tax reductions."""


def earlier_tax_reductions(income_tax, name: str) -> list:
    """The tax reductions listed before ``name`` in step_6_tax_reductions.

    ITA 2007 s. 29(2)-(3) allows each reduction only so far as there is Step 5
    tax left after the reductions already deducted. The order does not change
    their total, so the model deducts them in list order: each capped reduction
    takes the tax the ones before it leave. A reduction not in the list (a
    reform has removed it) comes after every listed one.
    """
    subtractions = list(income_tax.step_6_tax_reductions)
    if name in subtractions:
        return subtractions[: subtractions.index(name)]
    return subtractions
