def single_person_UC(sim):
    sim.add_person(
        name="adult", age=26, is_household_head=True, is_benunit_head=True
    )
    sim.add_benunit(adults=["adult"], claims_UC=True)
    sim.add_household(adults=["adult"])
    return sim


def couple_UC(sim):
    sim.add_person(
        name="adult", age=26, is_household_head=True, is_benunit_head=True
    )
    sim.add_person(name="adult_2", age=27)
    sim.add_benunit(adults=["adult", "adult_2"], claims_UC=True)
    sim.add_household(adults=["adult", "adult_2"])
    return sim


def single_person_UC_one_child(sim):
    sim.add_person(
        name="adult", age=26, is_household_head=True, is_benunit_head=True
    )
    sim.add_person(name="child", age=4)
    sim.add_benunit(adults=["adult"], children=["child"], claims_UC=True)
    sim.add_household(adults=["adult"], children=["child"])
    return sim


def couple_UC_one_child(sim):
    sim.add_person(
        name="adult", age=26, is_household_head=True, is_benunit_head=True
    )
    sim.add_person(name="adult_2", age=27)
    sim.add_person(name="child", age=4)
    sim.add_benunit(
        adults=["adult", "adult_2"], children=["child"], claims_UC=True
    )
    sim.add_household(adults=["adult", "adult_2"], children=["child"])
    return sim


def single_person_UC_two_children(sim):
    sim.add_person(
        name="adult", age=26, is_household_head=True, is_benunit_head=True
    )
    sim.add_person(name="child", age=4)
    sim.add_person(name="child_2", age=6)
    sim.add_benunit(
        adults=["adult"],
        children=["child", "child_2"],
        claims_UC=True,
        claims_CB=True,
    )
    sim.add_household(adults=["adult"], children=["child", "child_2"])
    return sim


def couple_UC_two_children(sim):
    sim.add_person(
        name="adult", age=26, is_household_head=True, is_benunit_head=True
    )
    sim.add_person(name="adult_2", age=27)
    sim.add_person(name="child", age=4)
    sim.add_person(name="child_2", age=6)
    sim.add_benunit(
        adults=["adult", "adult_2"],
        children=["child", "child_2"],
        claims_UC=True,
    )
    sim.add_household(
        adults=["adult", "adult_2"], children=["child", "child_2"]
    )
    return sim
