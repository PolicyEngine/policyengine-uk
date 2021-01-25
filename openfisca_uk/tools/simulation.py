import openfisca_uk
from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_core.periods import period
import pandas as pd
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_uk.tools.internals import VariableGraph
from openfisca_core import periods
from openfisca_survey_manager.scenarios import AbstractSurveyScenario
import numpy as np
import os
import warnings

try:
    import frs
except:
    pass
import copy

warnings.filterwarnings("ignore")


class IndividualSim:
    def __init__(self, *reforms):
        self.reforms = reforms
        self.tax_benefit_system = openfisca_uk.CountryTaxBenefitSystem()
        self.entities = {
            var.key: var for var in self.tax_benefit_system.entities
        }
        for reform in reforms:
            self.tax_benefit_system = reform(self.tax_benefit_system)
        self.situation_data = {"people": {}, "benunits": {}, "households": {}}
        self.varying = False
        self.num_points = None

    def build(self):
        self.sim_builder = SimulationBuilder()
        system = openfisca_uk.CountryTaxBenefitSystem()
        for reform in self.reforms:
            system = reform(system)
        self.sim = self.sim_builder.build_from_entities(
            system, self.situation_data
        )

    def add_data(
        self,
        entity="people",
        name=None,
        input_period="2020",
        auto_period=True,
        **kwargs,
    ):
        entity_plural = self.entities[entity].plural
        if name is None:
            name = (
                entity + "_" + str(len(self.situation_data[entity_plural]) + 1)
            )
        if auto_period:
            data = {}
            for var, value in kwargs.items():
                try:
                    def_period = self.tax_benefit_system.get_variable(
                        var
                    ).definition_period
                    if def_period in ["eternity", "year"]:
                        input_periods = [input_period]
                    else:
                        input_periods = period(input_period).get_subperiods(
                            def_period
                        )
                    data[var] = {
                        str(subperiod): value for subperiod in input_periods
                    }
                except:
                    data[var] = value
        self.situation_data[entity_plural][name] = data
        self.build()

    def add_person(self, **kwargs):
        self.add_data(entity="person", **kwargs)

    def add_benunit(self, **kwargs):
        self.add_data(entity="benunit", **kwargs)

    def add_household(self, **kwargs):
        self.add_data(entity="household", **kwargs)

    def get_entity(self, name):
        entity_type = [
            entity
            for entity in self.entities.values()
            if name in self.situation_data[entity.plural]
        ][0]
        return entity_type

    def get_group(self, entity, name):
        containing_entity = [
            group
            for group in self.situation_data[entity.plural]
            if name in self.situation_data[entity.plural][group]["adults"]
            or name in self.situation_data[entity.plural][group]["children"]
        ][0]
        return containing_entity

    def calc(self, var, period="2020", target=None, index=None):
        entity = self.sim_builder.get_variable_entity(var)
        if target is not None:
            target_entity = self.get_entity(target)
            if target_entity.key != entity.key:
                target = self.get_group(entity, target)
        try:
            result = self.sim.calculate(var, period)
        except:
            try:
                result = self.sim.calculate_add(var, period)
            except:
                result = self.sim.calculate_divide(var, period)
        if self.varying:
            result = result.reshape(
                (self.num_points, len(self.situation_data[entity.plural]))
            ).transpose()
        members = list(self.situation_data[entity.plural])
        if index is not None:
            index = min(len(members) - 1, index)
        if target is not None:
            index = members.index(target)
        if target is not None or index is not None:
            return result[index]
        return result

    def calc_deriv(self, var, wrt="earnings", period="2020", target=None):
        y = self.calc(var, period=period, target=target)
        x = self.calc(wrt, period=period, target=target)
        assert (
            len(y) > 1 and len(x) > 1
        ), "Simulation must vary on an axis to calculate derivatives."
        deriv = (y[1:] - y[:-1]) / (x[1:] - x[:-1])
        deriv = np.append(deriv, deriv[-1])
        return deriv

    def calc_mtr(self, target=None):
        return 1 - self.calc_deriv(
            "household_net_income", wrt="earnings", target=target
        )

    def reset_vary(self):
        del self.situation_data["axes"]
        self.varying = False
        self.num_points = None

    def vary(self, var, min=0, max=200000, step=100, index=0, period="2020"):
        if "axes" not in self.situation_data:
            self.situation_data["axes"] = [[]]
        count = int((max - min) / step)
        self.situation_data["axes"][0] += [
            {
                "count": count,
                "name": var,
                "min": min,
                "max": max,
                "period": period,
                "index": index,
            }
        ]
        self.build()
        self.varying = True
        self.num_points = count

class UKSurveyScenario(AbstractSurveyScenario):
    def __init__(self, tax_benefit_system = None, baseline_tax_benefit_system = None,
            data = None, year = None):
        super(UKSurveyScenario, self).__init__()
        if tax_benefit_system is None:
            tax_benefit_system = UKTaxBenefitSystem()
        self.set_tax_benefit_systems(
            tax_benefit_system = tax_benefit_system,
            baseline_tax_benefit_system = baseline_tax_benefit_system,
            )
        self.year = year
        self.varying_variable = "earnings"
        self.weight_variable_by_entity = {
            "person": "adult_weight",
            "benunit": "benunit_weight",
            "household": "household_weight"
        }
        self.role_variable_by_entity_key = {
            "benunit": "role",
            "household": "role",
            }
        self.mtr_group = "household"
        if data is None:
            return

        input_data_frame_by_entity_by_period = data['input_data_frame_by_entity_by_period']
        for period, input_data_frame_by_entity in input_data_frame_by_entity_by_period.items():
            entity_variables = [set(df.columns) for df in input_data_frame_by_entity.values()]

        variables_from_data = set.union(*entity_variables)
        self.used_as_input_variables = list(
            set(tax_benefit_system.variables.keys()).intersection(
                set(variables_from_data)
                )
            )
        self.used_as_input_variables = set(self.used_as_input_variables)
        self.init_from_data(data = data, use_marginal_tax_rate=True)

class SurveySim:
    def __init__(self, *reforms, year=2020):
        self.reforms = reforms
        self.year = year
        self.data = self.build_entity_dataframe()
        self.tax_benefit_system = openfisca_uk.CountryTaxBenefitSystem()
        for reform in reforms:
            self.tax_benefit_system = reform(self.tax_benefit_system)
        self.scenario = UKSurveyScenario(tax_benefit_system=self.tax_benefit_system, data=self.data, year=self.year)

    def calc(self, variable, period="2020", map_to=None):
        values = self.scenario.calculate_variable(variable, period)
        entity_key = self.tax_benefit_system.variables[variable].entity.key
        if map_to is None or map_to == entity_key:
            return values
        original_entities = self.scenario.simulation.populations[entity_key]
        target_entities = self.scenario.simulation.populations[map_to]
        if map_to == "person":
            return original_entities.project(values)
        if "benunit" in [entity_key, map_to] and "household" in [entity_key, map_to]:
            personal_averages = original_entities.project(values) / original_entities.project(original_entities.nb_persons())
            return target_entities.sum(personal_averages)
        return target_entities.sum(values)
    
    def build_entity_dataframe(self):
        person, benunit, household = frs.load()
        del household["country"]
        input_data_frame_by_entity = dict(person=person, benunit=benunit, household=household)
        person["role"] = person["role"].replace({"adult": 0, "child": 1})
        input_data_frame_by_entity_by_period = {periods.period(self.year): input_data_frame_by_entity}
        data = dict()
        data['input_data_frame_by_entity_by_period'] = input_data_frame_by_entity_by_period
        return data


class PopulationSim:
    def __init__(self, *reforms, frs_data=None, input_period="2020"):
        self.reforms = reforms
        self.input_period = input_period
        self.simulation = self.load_frs(frs_data=frs_data)
        self.populations = self.simulation.populations
        self.benunits = self.simulation.populations["benunit"]
        self.households = self.simulation.populations["household"]
        self.variables = self.simulation.tax_benefit_system.variables
    
    def get_entity(self, var):
        return self.variables[var].entity.key

    def calc(self, var, period="2020", copy_to_members=False, share_among_members=False, sum_by=None, average_by=None):
        result = self.simulation.calculate(var, period)
        entity = self.get_entity(var)
        population = self.populations[entity]
        if copy_to_members and entity != "person":
            return population.project(result)
        elif share_among_members and entity != "person":
            return population.project(result) / population.nb_persons()
        elif sum_by is not None and entity == "person":
            return self.populations[sum_by].sum(result)
        elif average_by is not None and entity == "person":
            return self.populations[average_by].sum(result) / self.populations[average_by].nb_persons()
        return result

    def df(self, cols, map_to="person"):
        df = {}
        for var in cols:
            df[var] = self.calc(var, map_to=map_to)
        return pd.DataFrame(df)

    def load_frs(self, frs_data=None, verbose=False, change={}):
        """
        Create and populate a tax-benefit simulation model from OpenFisca.

        Arguments:
            reforms: any reforms to apply, in order.
            data: any data to use instead of the loaded Family Resources Survey.
            input_period: the period in which to enter all data (at the moment, all data is entered under this period).

        Returns:
            A Simulation object.
        """
        system = openfisca_uk.CountryTaxBenefitSystem()
        for reform in self.reforms:
            system = reform(system)  # apply each reform in order
        builder = SimulationBuilder()
        builder.create_entities(
            system
        )  # create the entities (person, benunit, etc.)
        if not frs_data:
            person_file, benunit_file, household_file = frs.load()
        else:
            person_file, benunit_file, household_file = frs_data
        person_ids = np.array(person_file["person_id"])
        benunit_ids = np.array(benunit_file["benunit_id"])
        household_ids = np.array(household_file["household_id"])
        builder.declare_person_entity("person", person_ids)
        benunits = builder.declare_entity("benunit", benunit_ids)
        households = builder.declare_entity("household", household_ids)
        person_roles = np.where(person_file["is_adult"], "adult", "child")
        builder.join_with_persons(
            benunits, np.array(person_file["benunit_id"]), person_roles
        )
        builder.join_with_persons(
            households, np.array(person_file["household_id"]), person_roles
        )
        model = builder.build(system)
        skipped = []
        for input_file in [person_file, benunit_file, household_file]:
            for column in input_file.columns:
                if column in change:
                    input_file[column] += change[column]
                if column != "role":
                    try:
                        model.set_input(column, self.input_period, np.array(input_file[column]))
                    except Exception as e:
                        skipped += [column]
        if skipped and verbose:
            print(
                f"Incomplete initialisation: skipped {len(skipped)} variables:"
            )
            for var in skipped:
                print(f"{var}")
        return model

    def entity_df(self, entity="benunit"):
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
        df = pd.DataFrame()
        variables = self.model.tax_benefit_system.variables.keys()
        entity_variables = list(
            filter(
                lambda x: self.model.tax_benefit_system.variables[x].entity.key
                == entity,
                variables,
            )
        )
        for var in entity_variables:
            def_period = self.model.tax_benefit_system.get_variable(
                var
            ).definition_period
            if def_period in ["eternity", "year"]:
                inp_period = self.input_period
            else:
                inp_period = period(self.input_period).get_subperiods(
                    def_period
                )[-1]
            df[var] = self.model.calculate(var, inp_period)
        return df

    def calc_mtr(self, return_change_df=False):
        EARNINGS_BONUS_PER_YEAR = 100
        people = pd.DataFrame()
        people["person_id"] = self.calc("person_id")
        people["benunit_id"] = self.calc("benunit_id", map_to="person")
        index_in_benunit = people.groupby("benunit_id").cumcount()
        net_income = self.map_to(
            self.calc("net_income", map_to="benunit"),
            entity="benunit",
            target_entity="person",
        )
        mtrs = np.zeros_like(people["person_id"], dtype=float)
        bonuses = np.zeros_like(people["person_id"], dtype=float)
        for i in range(2):
            with np.errstate(divide="ignore"):
                bonus_amount = (
                    (index_in_benunit == i)
                    * EARNINGS_BONUS_PER_YEAR
                    * self.calc("is_adult")
                )
                bonus_sim = PopulationSim(
                    *self.reforms,
                    input_period=self.input_period,
                )
                bonus_sim.model = bonus_sim.load_frs(
                    change={"earnings": bonus_amount}
                )
                bonus_given_to_benunit = self.map_to(
                    bonus_sim.calc("earnings", map_to="benunit"),
                    entity="benunit",
                    target_entity="person",
                ) - self.map_to(
                    self.calc("earnings", map_to="benunit"),
                    entity="benunit",
                    target_entity="person",
                )
                new_net_income = self.map_to(
                    bonus_sim.calc("net_income", map_to="benunit"),
                    entity="benunit",
                    target_entity="person",
                )
                if return_change_df:
                    CHANGE_VARS = [
                        "earnings",
                        "taxable_income",
                        "gross_income",
                        "net_income",
                        "income_tax",
                        "NI",
                        "tax_credits",
                        "child_benefit",
                        "housing_benefit",
                        "income_support",
                        "JSA_income",
                        "pension_credit",
                        "ESA_income",
                        "universal_credit",
                    ]
                    changes = {}
                    for var in CHANGE_VARS:
                        original_amount = self.map_to(
                            self.calc(var, map_to="benunit"),
                            entity="benunit",
                            target_entity="person",
                        )
                        new_amount = self.map_to(
                            bonus_sim.calc(var, map_to="benunit"),
                            entity="benunit",
                            target_entity="person",
                        )
                        changes[var] = new_amount - original_amount
                        changes[var + "_original"] = original_amount
                        changes[var + "_new"] = new_amount
                change = new_net_income - net_income
                mtr_calculated = (bonus_amount > 0) * (
                    bonus_given_to_benunit == 100
                )
                mtr = np.where(mtr_calculated, 1 - (change / bonus_amount), 0)
                mtrs += np.round(mtr, 2)
                bonuses += bonus_amount
        mtrs = np.where(self.calc("is_adult"), mtrs, np.nan)
        if not return_change_df:
            return mtrs
        else:
            df = pd.DataFrame()
            df["MTR"] = mtrs
            for var in changes:
                df[var] = changes[var]
            df["earnings"] = self.calc("taxable_income")
            return df
