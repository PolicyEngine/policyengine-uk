import pandas as pd
from openfisca_uk import CountryTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_uk.reforms.marginal_tax_rates.head_bonus import (
    small_earnings_increase_for_head,
)
from openfisca_uk.reforms.marginal_tax_rates.non_head_bonus import (
    small_earnings_increase_for_non_head,
)
from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np
import os
import pandas as pd


def model(*reforms, data_dir="inputs", period="ETERNITY"):
    """
    Create and populate a tax-benefit simulation model from OpenFisca.

    Arguments:
        reforms: any reforms to apply, in order.
        data: any data to use instead of the loaded Family Resources Survey.
        period: the period in which to enter all data (at the moment, all data is entered under this period).

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
    if data_dir is None:
        data_dir = "inputs"
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
    model = builder.build(system)
    for column in person_file.columns:
        if "_id" not in column and column != "role":
            model.set_input(
                column, period, np.array(person_file[column])
            )  # input data for person data
    for column in benunit_file.columns:
        if "_id" not in column and column != "role":
            model.set_input(
                column, period, np.array(benunit_file[column])
            )  # input data for benunit data
    for column in household_file.columns:
        if "_id" not in column and column != "role":
            model.set_input(
                column, period, np.array(household_file[column])
            )  # input data for household data
    return model


def calc_mtr(*reforms, var="person_benunit_net_income", period="2020-10-18"):
    baseline = model(*reforms)
    current_net_income = baseline.calculate(var, period)
    head_given_bonus = model(*reforms, small_earnings_increase_for_head)
    head_bonus = head_given_bonus.calculate("taxed_means_tested_bonus", period)
    new_head_net_income = head_given_bonus.calculate(var, period)
    non_head_given_bonus = model(
        *reforms, small_earnings_increase_for_non_head
    )
    non_head_bonus = non_head_given_bonus.calculate(
        "taxed_means_tested_bonus", period
    )
    new_non_head_net_income = non_head_given_bonus.calculate(var, period)
    new_net_income = new_head_net_income * (
        head_bonus > 0
    ) + new_non_head_net_income * (non_head_bonus > 0)
    with np.errstate(divide="ignore"):
        marginal_tax_rate = 1 - (new_net_income - current_net_income) / (
            head_bonus + non_head_bonus
        )
    invalid = np.isinf(marginal_tax_rate)
    marginal_tax_rate[invalid] = 0
    return marginal_tax_rate


def entity_df(model, entity="benunit", period="2020-10-18"):
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
        df[var] = model.calculate(var, period)
    return df
