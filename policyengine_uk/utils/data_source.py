def built_from_data(simulation) -> bool:
    """Whether a simulation was built from survey or other microdata rather
    than from a situation dictionary.

    Variables that impute unobserved detail across a population read this,
    not the sum of weights: a region or constituency filtered from the data
    carries little weight and is still data. policyengine_uk.Simulation
    records it as ``built_from_dataset``, and its builders keep it current. A
    policyengine-core Simulation built over the UK system records
    ``is_over_dataset``, which core's SimulationBuilder leaves set if it later
    overwrites that simulation in place with a situation.
    """
    flag = getattr(simulation, "built_from_dataset", None)
    if flag is None:
        flag = getattr(simulation, "is_over_dataset", False)
    return bool(flag)
