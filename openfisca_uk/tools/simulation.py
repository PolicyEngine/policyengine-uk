from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_core.periods import period
import pandas as pd
from openfisca_uk import CountryTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder
import numpy as np
import os


def load_frs(*reforms, data_dir="frs", input_period="2020"):
    """
    Create and populate a tax-benefit simulation model from OpenFisca.

    Arguments:
        reforms: any reforms to apply, in order.
        data: any data to use instead of the loaded Family Resources Survey.
        input_period: the period in which to enter all data (at the moment, all data is entered under this period).

    Returns:
        A Simulation object.
    """
    system = CountryTaxBenefitSystem()
    for reform in reforms:
        system = reform(system)  # apply each reform in order
    builder = SimulationBuilder()
    builder.create_entities(
        system
    )  # create the entities (person, benunit, etc.)
    person_file = pd.read_csv(
        os.path.join(data_dir, "person.csv"), low_memory=False
    )
    benunit_file = pd.read_csv(
        os.path.join(data_dir, "benunit.csv"), low_memory=False
    )
    household_file = pd.read_csv(
        os.path.join(data_dir, "household.csv"), low_memory=False
    )
    person_ids = np.array(person_file["person_id"])
    benunit_ids = np.array(benunit_file["benunit_id"])
    household_ids = np.array(household_file["household_id"])
    builder.declare_person_entity("person", person_ids)
    benunits = builder.declare_entity("benunit", benunit_ids)
    households = builder.declare_entity("household", household_ids)
    person_roles = person_file["role"]
    builder.join_with_persons(
        benunits, np.array(person_file["benunit_id"]), person_roles
    )  # define person-benunit memberships
    builder.join_with_persons(
        households, np.array(person_file["household_id"]), person_roles
    )
    person_file["index"] = np.arange(start=0, stop=len(person_file))
    model = builder.build(system)
    skipped = []
    for input_file in [person_file, benunit_file, household_file]:
        for column in input_file.columns:
            if column != "role":
                try:
                    def_period = system.get_variable(column).definition_period
                    if def_period in ["eternity", "year"]:
                        input_periods = [input_period]
                    else:
                        input_periods = period(input_period).get_subperiods(
                            def_period
                        )
                    for subperiod in input_periods:
                        model.set_input(
                            column, subperiod, np.array(input_file[column])
                        )
                except Exception as e:
                    skipped += [column]
    if skipped:
        print(f"Incomplete initialisation: skipped {len(skipped)} variables:")
        for var in skipped:
            print(f"{var}")
    return model


def entity_df(model, entity="benunit", input_period="2020"):
    """
    Create and populate a DataFrame with all variables in the simulation

    Arguments:
        model: the model to use.
        entity: the entity to calculate variables for.
        period: the period for which to calculate all data.

    Returns:
        A DataFrame
    """
    if entity not in ["benunit", "person", "household"]:
        raise Exception("Unsupported entity.")
    if entity == "benunit":
        weight_col = "benunit_weight"
    elif entity == "person":
        weight_col = "adult_weight"
    else:
        weight_col = "household_weight"
    df = pd.DataFrame()
    variables = model.tax_benefit_system.variables.keys()
    entity_variables = list(
        filter(
            lambda x: model.tax_benefit_system.variables[x].entity.key
            == entity,
            variables,
        )
    )
    for var in entity_variables:
        def_period = model.tax_benefit_system.get_variable(
            var
        ).definition_period
        if def_period in ["eternity", "year"]:
            inp_period = input_period
        else:
            inp_period = period(input_period).get_subperiods(def_period)[-1]
        df[var] = model.calculate(var, inp_period)
    return df
