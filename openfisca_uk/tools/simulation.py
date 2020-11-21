from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_core.periods import period
import pandas as pd
from openfisca_uk import CountryTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder
import numpy as np
import os
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

class Simulation:
    def __init__(self, *reforms, data_dir="frs", input_period="2020"):
        self.data_dir = data_dir
        self.input_period = input_period
        self.model = self.load_frs(*reforms)

    def calc(self, var, map_to_person=False, period="2020"):
        try:
            result = self.model.calculate(var, period)
        except:
            result = self.model.calculate_add(var, period)
        entity = self.model.tax_benefit_system.variables[var].entity.key
        if map_to_person and entity != "person":
            person_df = pd.DataFrame()
            entity_df = pd.DataFrame()
            entity_df["entity_id"] = self.relations[entity]
            entity_df["values"] = result
            person_df["person_id"] = self.relations["person"]
            person_df["entity_id"] = self.relations[f"person-{entity}"]
            person_df.set_index("person_id")
            entity_df.set_index("entity_id")
            df = person_df.merge(entity_df, on="entity_id")
            df.set_index("person_id")
            return np.array(df["values"])
        else:
            ids = self.relations[self.model.tax_benefit_system.variables[var].entity.key]
            sort = np.sort(ids)
            order = np.argsort(ids)
            test = ids[order]
            values = result[order]
            return values
    
    
    def df(self, include_mtr=False):
        person = self.entity_df(self.model, entity="person").set_index("person_id")
        person["benunit_id"] = self.relations["person-benunit"]
        person["household_id"] = self.relations["person-household"]
        if include_mtr:
            person["MTR"] = self.calc_mtr()
        benunit = self.entity_df(self.model, entity="benunit").set_index("benunit_id")
        household = self.entity_df(self.model, entity="household").set_index("household_id")
        df = person.join(benunit, on="benunit_id").join(household, on="household_id")
        return df

    def load_frs(self, *reforms, verbose=False, bonus={}):
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
            os.path.join(self.data_dir, "person.csv"), low_memory=False
        )
        benunit_file = pd.read_csv(
            os.path.join(self.data_dir, "benunit.csv"), low_memory=False
        )
        household_file = pd.read_csv(
            os.path.join(self.data_dir, "household.csv"), low_memory=False
        )
        person_file.sort_values(by=["person_id"], inplace=True)
        benunit_file.sort_values(by=["benunit_id"], inplace=True)
        household_file.sort_values(by=["household_id"], inplace=True)
        for input_file in [person_file, benunit_file, household_file]:
            input_file = input_file.sort_index()
        self.relations = {
            "person": np.array(person_file["person_id"]),
            "benunit": np.array(benunit_file["benunit_id"]),
            "household": np.array(household_file["household_id"]),
            "person-benunit": np.array(person_file["benunit_id"]),
            "person-household": np.array(person_file["household_id"])
        }
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
                if column in bonus:
                    input_file[column] += bonus[column]
                if column != "role":
                    try:
                        def_period = system.get_variable(column).definition_period
                        if def_period in ["eternity", "year"]:
                            input_periods = [self.input_period]
                        else:
                            input_periods = period(self.input_period).get_subperiods(
                                def_period
                            )
                        for subperiod in input_periods:
                            model.set_input(
                                column, subperiod, np.array(input_file[column])
                            )
                    except Exception as e:
                        skipped += [column]
        if skipped and verbose:
            print(f"Incomplete initialisation: skipped {len(skipped)} variables:")
            for var in skipped:
                print(f"{var}")
        return model


    def entity_df(self, model, entity="benunit"):
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
                inp_period = self.input_period
            else:
                inp_period = period(self.input_period).get_subperiods(def_period)[-1]
            df[var] = model.calculate(var, inp_period)
        return df

    def calc_mtr(self, *reforms, return_change_df=False):
        baseline = self.load_frs(*reforms)
        household_net_income = self.calc("household_net_income_ahc", map_to_person=True)
        MAX_PEOPLE_IN_HOUSEHOLD = 9
        EARNINGS_BONUS_PER_YEAR = 100
        person_id = self.calc("person_id")
        person_number = person_id % 100000
        mtrs = np.zeros_like(person_id, dtype=float)
        bonuses = np.zeros_like(person_id, dtype=float)
        change_vars = ["earnings", "household_net_income", "income_tax", "NI", "working_tax_credit", "child_tax_credit", "pension_credit", "income_support", "JSA_income", "ESA_income", "housing_benefit", "universal_credit"]
        for i in tqdm(range(MAX_PEOPLE_IN_HOUSEHOLD), desc="Calculating MTRs for household members"):
            with np.errstate(divide="ignore"):
                bonus_amount = (person_number == i + 1) * EARNINGS_BONUS_PER_YEAR
                bonus_sim = Simulation(*reforms, data_dir=self.data_dir, input_period=self.input_period)
                bonus_sim.model = bonus_sim.load_frs(bonus={"earnings": bonus_amount})
                new_household_net_income = bonus_sim.calc("household_net_income_ahc", map_to_person=True)
                changes = {}
                for var in change_vars:
                    changes[var] = bonus_sim.calc(var, map_to_person=True) - self.calc(var, map_to_person=True)
                change = new_household_net_income - household_net_income
                mtr = np.where(bonus_amount > 0, 1 - (change / bonus_amount), 0)
                mtrs += mtr
                bonuses += bonus_amount
        if not return_change_df:
            return mtrs
        else:
            df = pd.DataFrame()
            df["MTR"] = mtrs
            for var in change_vars:
                df[var] = changes[var]
            df["earnings"] = self.calc("taxable_income")
            return df
