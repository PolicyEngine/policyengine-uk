def built_from_data(simulation) -> bool:
    """Whether a simulation was built from survey or other microdata rather
    than from a situation dictionary.

    Variables that impute unobserved detail across a population read this,
    not the sum of weights: a region or constituency filtered from the data
    carries little weight and is still data. policyengine_uk.Simulation
    records it as ``built_from_dataset``, and its builders keep it current. A
    policyengine-core Simulation built over the UK system records
    ``is_over_dataset``.

    Known limitation in policyengine-core 3.33.2: directly overwriting a
    data-built simulation with ``SimulationBuilder.build_from_dict`` leaves
    its source flags and dataset unchanged and records no new situation
    marker. This helper therefore still returns True for that unsupported
    overwrite, its clones and branches, and a UK simulation overwritten by
    the core builder. Use UK's ``build_from_situation`` for in-place rebuilds;
    it resets the source flag correctly.
    """
    flag = getattr(simulation, "built_from_dataset", None)
    if flag is None:
        flag = getattr(simulation, "is_over_dataset", False)
    return bool(flag)
