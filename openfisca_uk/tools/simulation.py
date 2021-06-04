import openfisca_uk
from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_core.periods import period
import pandas as pd
from openfisca_core.simulation_builder import SimulationBuilder
import numpy as np
import warnings
import microdf as mdf

try:
    import frs
except:
    pass
import copy

warnings.filterwarnings("ignore")

np.random.seed(0)


class IndividualSim:
    def __init__(self, *reforms, year=2018):
        self.year = year
        self.reforms = reforms
        self.system = openfisca_uk.CountryTaxBenefitSystem()
        self.entities = {var.key: var for var in self.system.entities}
        self.apply_reforms(self.reforms)
        self.situation_data = {"people": {}, "benunits": {}, "households": {}}
        self.varying = False
        self.num_points = None

    def build(self):
        self.sim_builder = SimulationBuilder()
        self.system = openfisca_uk.CountryTaxBenefitSystem()
        self.apply_reforms(self.reforms)
        self.sim = self.sim_builder.build_from_entities(
            self.system, self.situation_data
        )

    def apply_reforms(self, reforms: list) -> None:
        """Applies a list of reforms to the tax-benefit system.

        Args:
            reforms (list): A list of reforms. Each reform can also be a list of reforms.
        """
        for reform in reforms:
            if isinstance(reform, tuple) or isinstance(reform, list):
                self.apply_reforms(reform)
            else:
                self.system = reform(self.system)

    def add_data(
        self,
        entity="people",
        name=None,
        input_period=None,
        auto_period=True,
        **kwargs,
    ):
        input_period = input_period or self.year
        entity_plural = self.entities[entity].plural
        if name is None:
            name = (
                entity + "_" + str(len(self.situation_data[entity_plural]) + 1)
            )
        if auto_period:
            data = {}
            for var, value in kwargs.items():
                try:
                    def_period = self.system.get_variable(
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
        self.add_data(entity="benunit", name="benunit", **kwargs)

    def add_household(self, **kwargs):
        self.add_data(entity="household", name="household", **kwargs)

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

    def calc(self, var, period=None, target=None, index=None):
        period = period or self.year
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

    def calc_deriv(
        self,
        var,
        wrt="employment_income",
        period=None,
        var_target=None,
        wrt_target=None,
    ):
        period = period or self.year
        y = self.calc(var, period=period, target=var_target)
        x = self.calc(wrt, period=period, target=wrt_target)
        try:
            y = y.squeeze()
        except:
            pass
        try:
            x = x.squeeze()
        except:
            pass
        x = x.astype(np.float32)
        y = y.astype(np.float32)
        assert (
            len(y) > 1 and len(x) > 1
        ), "Simulation must vary on an axis to calculate derivatives."
        deriv = (y[1:] - y[:-1]) / (x[1:] - x[:-1])
        deriv = np.append(deriv, deriv[-1])
        return deriv

    def calc_mtr(
        self,
        target="household_net_income",
        wrt="employment_income",
        wrt_target=None,
        var_target=None,
    ):
        return 1 - self.calc_deriv(
            target, wrt=wrt, wrt_target=wrt_target, var_target=var_target
        )

    def reset_vary(self):
        del self.situation_data["axes"]
        self.varying = False
        self.num_points = None

    def vary(self, var, min=0, max=200000, step=100, index=0, period=None):
        period = period or self.year
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


class PopulationSim:
    def __init__(
        self, *reforms, frs_data=None, input_period="2020", use_microdf=False
    ):
        warnings.warn(
            "PopulationSim is deprecated and will be removed in a future release. Please use Microsimulation instead for improved microdata handling and transparency."
        )
        self.reforms = reforms
        self.input_period = input_period
        self.model = self.load_frs(frs_data=frs_data)
        self.use_microdf = use_microdf
        self.weight_vars = None
        self.weight_vars = dict(
            person=self.calc("household_weight", map_to="person"),
            benunit=self.calc("benunit_weight"),
            household=self.calc("household_weight"),
        )

    def map_to(self, arr, entity="person", target_entity="benunit"):
        LEVELS = {"person": 1, "benunit": 2, "household": 3}
        if (
            not target_entity or LEVELS[target_entity] == LEVELS[entity]
        ):  # no change
            return arr
        elif target_entity == "person":  # group level -> person level
            person_df = pd.DataFrame()
            entity_df = pd.DataFrame()
            entity_df["entity_id"] = self.relations[entity]
            entity_df["values"] = arr
            person_df["person_id"] = self.relations["person"]
            person_df["entity_id"] = self.relations[f"person-{entity}"]
            person_df.set_index("person_id")
            entity_df.set_index("entity_id")
            df = person_df.merge(entity_df, on="entity_id")
            df.set_index("person_id")
            return np.array(df["values"])
        elif (
            entity == "person"
        ):  # person level -> (sum by group entity) -> group entity level
            df = pd.DataFrame()
            df["values"] = arr
            df["person_id"] = self.relations["person"]
            df["entity_id"] = self.relations[f"person-{target_entity}"]
            df = df.groupby(by="entity_id", as_index=False).sum()
            df.set_index("entity_id")
            return np.array(df["values"])
        else:  # benunit_level -> household_level and vice versa - assume equally distributed in source entity
            person_level = self.map_to(
                arr, entity=entity, target_entity="person"
            ) / self.calc("people_in_household", map_to="person")
            entity_level = self.map_to(
                person_level, entity="person", target_entity=target_entity
            )
            return entity_level

    def calc(self, var, map_to=None, period="2020", verbose=False):
        try:
            result = self.model.calculate(var, period)
        except:
            if verbose:
                print(
                    f"Initial period calculation failed for {var}; attempting to gross up periods"
                )
            try:
                result = self.model.calculate_add(var, period)
            except:
                if verbose:
                    print(
                        f"Grossing up period calculation failed for {var}; attempting to divide period"
                    )
                result = self.model.calculate_divide(var, period)
        entity = self.model.tax_benefit_system.variables[var].entity.key
        result = self.map_to(result, entity=entity, target_entity=map_to)
        if not self.use_microdf or self.weight_vars is None:
            return result
        return mdf.MicroSeries(
            result, weights=self.weight_vars[map_to or entity]
        )

    def decache(self, var, period):
        self.model.get_variable_population(var).get_holder(var).delete_arrays(
            period
        )

    def df(self, cols, map_to="person"):
        df = {}
        for var in cols:
            df[var] = self.calc(var, map_to=map_to)
        return mdf.MicroDataFrame(df, weights=self.weight_vars[map_to])

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
        person_file.sort_values("person_id", inplace=True)
        benunit_file.sort_values("benunit_id", inplace=True)
        household_file.sort_values("household_id", inplace=True)
        person_file["id"] = person_file["person_id"]
        benunit_file["id"] = benunit_file["benunit_id"]
        household_file["id"] = household_file["household_id"]
        person_file.sort_values("id", inplace=True)
        person_file.reset_index(inplace=True, drop=True)
        benunit_file.sort_values("id", inplace=True)
        benunit_file.reset_index(inplace=True, drop=True)
        household_file.sort_values("id", inplace=True)
        household_file.reset_index(inplace=True, drop=True)
        self.relations = {
            "person": np.array(person_file["person_id"]),
            "benunit": np.array(benunit_file["benunit_id"]),
            "household": np.array(household_file["household_id"]),
            "person-benunit": np.array(person_file["benunit_id"]),
            "person-household": np.array(person_file["household_id"]),
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
        model = builder.build(system)
        skipped = []
        for input_file in [person_file, benunit_file, household_file]:
            for column in input_file.columns:
                if column in change:
                    input_file[column] += change[column]
                if column != "role":
                    try:
                        def_period = system.get_variable(
                            column
                        ).definition_period
                        if def_period in ["eternity", "year"]:
                            input_periods = [self.input_period]
                        else:
                            input_periods = period(
                                self.input_period
                            ).get_subperiods(def_period)
                        for subperiod in input_periods:
                            model.set_input(
                                column, subperiod, np.array(input_file[column])
                            )
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
