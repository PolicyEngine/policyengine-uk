# Standard library imports
import copy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# PolicyEngine core imports
from policyengine_core.parameters import ParameterNode
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import (
    uprate_parameters,
)
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.variables import Variable

# PolicyEngine UK imports
from policyengine_uk.entities import BenUnit, Household, Person
from policyengine_uk.parameters.gov.contrib.create_private_pension_uprating import (
    add_private_pension_uprating_factor,
)
from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    add_triple_lock,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_september_cpi_uprating import (
    add_september_cpi_uprating,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    create_economic_assumption_indices,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    add_statutory_uprating_inputs,
)
from policyengine_uk.parameters.gov.hmrc.create_threshold_indexation import (
    add_threshold_indexation,
)
from policyengine_uk.parameters.gov.economic_assumptions.lag_average_earnings import (
    add_lagged_earnings,
)
from policyengine_uk.parameters.gov.economic_assumptions.lag_cpi import (
    add_lagged_cpi,
)
from policyengine_uk.parameters.gov.simulation.labour_supply_responses.aliases import (
    add_lsr_deprecation_aliases,
)
from policyengine_uk.utils.dated_reforms import (
    ParameterAssignment,
    Timeline,
    requires_projection,
    snapshot_timelines,
    tree_defines,
    write_assignment,
)
from policyengine_uk.utils.parameters import (
    add_removed_parameter_aliases,
    backdate_parameters,
    convert_to_fiscal_year_parameters,
)

# Module constants
COUNTRY_DIR = Path(__file__).parent
DEFAULT_DATASET_ENV_VAR = "POLICYENGINE_UK_DEFAULT_DATASET"

# Cache for fully-processed parameter tree, so convert_to_fiscal_year_parameters
# (22,538 param.update() calls) only runs once per process.
_processed_parameters_cache = None
# The parameters as loaded from the YAML files, before processing: each
# parameter's statutory values at their legal dates. Reforms are written
# onto a copy of this tree.
_statutory_parameters_cache = None
# Each gov parameter's timeline in the cached processed tree after
# projection (uprating, indexation and the other generated series) and
# before fiscal-year annualisation, by name.
_projected_timelines_cache = None


def process_parameter_tree(
    parameters: ParameterNode,
    baseline_parameters: Optional[ParameterNode] = None,
    annualise: bool = True,
) -> Tuple[ParameterNode, Dict[str, Timeline]]:
    """Project and annualise a statutory parameter tree.

    Applies, in order:
    - private pension uprating factors
    - lagged earnings and CPI indices
    - statutory uprating inputs (September CPI, May-July earnings)
    - triple lock calculations for state pensions
    - September CPI uprating
    - economic assumption indices
    - income tax and NICs threshold indexation after the freeze
    - parameter uprating and backdating
    - conversion to fiscal year parameters

    Returns the tree and each gov parameter's timeline just before the
    conversion to fiscal years.

    ``parameters.baseline`` is the current-law copy that ``baseline_vat``
    and the budget adjustments compare against. Without
    ``baseline_parameters`` it is a copy of this tree taken before uprating,
    which is current law only when the tree carries no reform. A reformed
    tree passes the processed current-law parameters as
    ``baseline_parameters``, whose ``baseline`` child it takes (#2188).
    ``annualise=False`` stops after the projection and adds no baseline.
    """
    parameters = add_private_pension_uprating_factor(parameters)
    parameters = add_lagged_earnings(parameters)
    parameters = add_lagged_cpi(parameters)
    parameters = add_statutory_uprating_inputs(parameters)
    parameters = add_triple_lock(parameters)
    parameters = add_september_cpi_uprating(parameters)
    parameters = create_economic_assumption_indices(parameters)
    parameters = add_threshold_indexation(parameters)
    parameters = add_lsr_deprecation_aliases(parameters)

    # Create baseline parameters for reform comparisons
    if annualise and baseline_parameters is None:
        parameters.add_child("baseline", parameters.clone())

    # Apply general parameter operations
    parameters = propagate_parameter_metadata(parameters)
    parameters = uprate_parameters(parameters)
    parameters = backdate_parameters(parameters, "2015-01-01")
    projected = snapshot_timelines(parameters.gov)
    if not annualise:
        return parameters, projected
    parameters.gov = convert_to_fiscal_year_parameters(parameters.gov)
    if baseline_parameters is not None:
        parameters.add_child("baseline", baseline_parameters.baseline.clone())
    return parameters, projected


class CountryTaxBenefitSystem(TaxBenefitSystem):
    """UK-specific tax and benefit system implementation.

    This class defines the UK tax-benefit system with all relevant
    variables, parameters, and entities (Person, BenUnit, Household).
    """

    basic_inputs: List[str] = [
        "brma",
        "local_authority",
        "region",
        "employment_income",
        "age",
    ]
    modelled_policies = COUNTRY_DIR / "programs.yaml"
    auto_carry_over_input_variables: bool = True

    variables: Dict[str, Variable]

    def reset_parameter_caches(self):
        """Reset all caches in the tax-benefit system."""
        self._parameters_at_instant_cache = {}
        for parameter in self.parameters.get_descendants():
            parameter._at_instant_cache = {}
        self.parameters._at_instant_cache = {}

    def reset_parameters(self) -> None:
        """Reset parameters by reloading from the parameters directory."""
        self._parameters_at_instant_cache = {}
        self.load_parameters(self.parameters_dir)
        self.parameters = add_removed_parameter_aliases(self.parameters)

    def process_parameters(
        self, baseline_parameters: Optional[ParameterNode] = None
    ) -> None:
        """Process and transform parameters with UK-specific adjustments.

        See ``process_parameter_tree``, which this runs on the system's
        parameters. ``projected_timelines`` keeps each gov parameter's
        timeline from before the conversion to fiscal years.
        """
        self._parameters_at_instant_cache = {}
        self.parameters, self.projected_timelines = process_parameter_tree(
            self.parameters, baseline_parameters
        )
        self.reset_parameter_caches()

    def apply_parameter_assignments(
        self, assignments: List[ParameterAssignment]
    ) -> None:
        """Rebuild the parameters with changes on the statutory timeline.

        Writes each change, in ``order``, onto a fresh copy of the
        parameters as loaded from the YAML files, then processes them as
        current law is processed, so each change is uprated, indexed and
        annualised by its parameter's rule. ``parameters.baseline`` stays
        current law. Where a bounded change has no stated value after it,
        prior law resumes along the path the parameter takes under the
        reform's other changes (see ``policyengine_uk.utils.dated_reforms``).
        """
        if not assignments:
            return
        baseline = processed_parameters()
        ordered = sorted(assignments, key=lambda assignment: assignment.order)
        projected = prior_law_projection(ordered)
        parameters = statutory_parameters()
        for assignment in ordered:
            write_assignment(
                parameters.get_child(assignment.path), assignment, projected
            )
        self.parameters = parameters
        self.process_parameters(baseline_parameters=baseline)

    def __init__(self):
        """Initialize the UK tax-benefit system with entities and parameters."""
        self._parameters_at_instant_cache: Dict[str, Any] = {}
        self.variables = {}

        # Create copies of entity classes to avoid modifying originals
        person, benunit, household = (
            copy.copy(Person),
            copy.copy(BenUnit),
            copy.copy(Household),
        )

        # Set up entities
        self.entities = [person, benunit, household]
        self.person_entity = person
        self.group_entities = [benunit, household]
        self.group_entity_keys = [entity.key for entity in self.group_entities]

        # Link entities to this tax-benefit system
        for entity in self.entities:
            entity.set_tax_benefit_system(self)

        self.variable_module_metadata = {}

        # Load all variables from the variables directory
        self.add_variables_from_directory(COUNTRY_DIR / "variables")

        # Set up and process parameters
        self.parameters_dir = COUNTRY_DIR / "parameters"
        global _processed_parameters_cache, _statutory_parameters_cache
        global _projected_timelines_cache
        if _processed_parameters_cache is not None:
            # Fast path: clone pre-processed parameters rather than re-running
            # the full pipeline (saves ~0.5s from convert_to_fiscal_year_parameters).
            # Reforms rebuild the parameters from the statutory tree through
            # apply_parameter_assignments, so they still get the full pipeline.
            self._parameters_at_instant_cache = {}
            self.parameters = _processed_parameters_cache.clone()
            self.projected_timelines = _projected_timelines_cache
        else:
            self.reset_parameters()
            _statutory_parameters_cache = self.parameters.clone()
            self.process_parameters()
            _processed_parameters_cache = self.parameters.clone()
            _projected_timelines_cache = self.projected_timelines


def _ensure_caches() -> None:
    if _processed_parameters_cache is None:
        CountryTaxBenefitSystem()


def processed_parameters() -> ParameterNode:
    """The processed current-law parameters (shared: do not change them)."""
    _ensure_caches()
    return _processed_parameters_cache


def statutory_parameters() -> ParameterNode:
    """A fresh copy of the parameters as loaded from the YAML files."""
    _ensure_caches()
    return _statutory_parameters_cache.clone()


def statutory_parameter_defines() -> Callable[[str], bool]:
    """Whether the statutory parameter tree has a parameter at a path."""
    _ensure_caches()
    return tree_defines(_statutory_parameters_cache)


def projected_timelines() -> Dict[str, Timeline]:
    """Current law's projected timeline for each gov parameter, by name."""
    _ensure_caches()
    return _projected_timelines_cache


def prior_law_projection(
    assignments: List[ParameterAssignment],
) -> Callable[[str], Optional[Timeline]]:
    """Prior law's projected timeline, by parameter name, for a reform.

    A bounded change with no stated value after it resumes along the path
    its parameter takes under the reform's other changes. That is current
    law's projection unless the reform also changes something else (a CPI
    forecast, say); then the other changes are projected first. Changes
    that themselves need the projection are left out of that first pass,
    so two such changes do not see each other.
    """
    current_law = projected_timelines()
    statutory = statutory_parameters()
    needing = [
        assignment
        for assignment in assignments
        if requires_projection(statutory.get_child(assignment.path), assignment)
    ]
    others = [assignment for assignment in assignments if assignment not in needing]
    if not needing or not others:
        return current_law.get
    for assignment in others:
        write_assignment(
            statutory.get_child(assignment.path), assignment, current_law.get
        )
    _, environment = process_parameter_tree(statutory, annualise=False)
    return environment.get


# Create system instance for module-level access
system = CountryTaxBenefitSystem()
parameters = system.parameters
variables = system.variables
