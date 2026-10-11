# Standard library imports
import copy
import logging
from collections import OrderedDict
from dataclasses import replace
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
    BACKDATED_FROM,
    LegacyOverride,
    ParameterAssignment,
    Timeline,
    apply_legacy_overrides,
    copy_timelines,
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

logger = logging.getLogger(__name__)

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


def _add_generated_parameters(parameters: ParameterNode) -> ParameterNode:
    parameters = add_private_pension_uprating_factor(parameters)
    parameters = add_lagged_earnings(parameters)
    parameters = add_lagged_cpi(parameters)
    parameters = add_statutory_uprating_inputs(parameters)
    parameters = add_triple_lock(parameters)
    parameters = add_september_cpi_uprating(parameters)
    parameters = create_economic_assumption_indices(parameters)
    parameters = add_threshold_indexation(parameters)
    parameters = add_lsr_deprecation_aliases(parameters)
    return parameters


def process_parameter_tree(
    parameters: ParameterNode,
    unreformed: Optional[ParameterNode] = None,
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

    ``parameters.baseline`` is the copy of the parameters without reforms
    that ``baseline_vat`` and the budget adjustments compare against, taken
    after the generated series are added and then uprated with the rest. A
    tree carrying dated reform changes passes ``unreformed``, the same tree
    without them, which the copy is taken from instead (#2188).
    ``annualise=False`` stops after the projection and adds no copy.
    """
    parameters = _add_generated_parameters(parameters)

    # Create baseline parameters for reform comparisons
    if annualise:
        baseline = (
            parameters.clone()
            if unreformed is None
            else _add_generated_parameters(unreformed)
        )
        parameters.add_child("baseline", baseline)

    # Apply general parameter operations
    parameters = propagate_parameter_metadata(parameters)
    parameters = uprate_parameters(parameters)
    parameters = backdate_parameters(parameters, BACKDATED_FROM)
    projected = snapshot_timelines(parameters.gov)
    if not annualise:
        return parameters, projected
    parameters.gov = convert_to_fiscal_year_parameters(parameters.gov)
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

    def process_parameters(self) -> None:
        """Process and transform parameters with UK-specific adjustments.

        See ``process_parameter_tree``, which this runs on the system's
        parameters. ``projected_timelines`` keeps each gov parameter's
        timeline from before the conversion to fiscal years.

        The system's dated reform changes (``dated_assignments``) are written
        onto the parameters first, so a modifier that reloads and edits the
        parameters before processing them again (as ``no_economic_assumptions``
        does) keeps the reform. Its legacy overrides of the annualised
        parameters are then applied again.
        """
        self._parameters_at_instant_cache = {}
        self._rebuild(self.parameters, statutory=False)
        self._apply_legacy_overrides()
        self.reset_parameter_caches()

    def apply_parameter_assignments(
        self, assignments: List[ParameterAssignment]
    ) -> None:
        """Rebuild the parameters with more changes on the statutory timeline.

        Adds the changes to the system's ``dated_assignments`` and writes
        them all, in order, onto a fresh copy of the parameters as loaded
        from the YAML files. The parameters are then processed as current law
        is, so each change is uprated, indexed and annualised by its
        parameter's rule, and ``parameters.baseline`` stays current law.
        Where a change reaches the part of a parameter's timeline that
        projection fills, prior law there follows the path the parameter
        takes under the reform's other changes (see
        ``policyengine_uk.utils.dated_reforms``).
        """
        if not assignments:
            return
        offset = len(self.dated_assignments)
        self.dated_assignments = self.dated_assignments + [
            replace(assignment, order=offset + index)
            for index, assignment in enumerate(
                sorted(assignments, key=lambda assignment: assignment.order)
            )
        ]
        self._parameters_at_instant_cache = {}
        key = _assignments_key(self.dated_assignments)
        cached = _rebuilt_parameters_cache.get(key)
        if cached is not None:
            self.parameters = cached[0].clone()
            self.projected_timelines = cached[1]
        else:
            self._rebuild(statutory_parameters(), statutory=True)
            _remember_rebuilt(key, self.parameters.clone(), self.projected_timelines)
        self._apply_legacy_overrides()
        self.reset_parameter_caches()

    def add_legacy_overrides(self, overrides: List[LegacyOverride]) -> None:
        """Apply changes to the annualised parameters and keep them.

        Kept so a later rebuild of the parameters applies them again, after
        the dated changes.
        """
        if not overrides:
            return
        self.legacy_overrides = self.legacy_overrides + list(overrides)
        apply_legacy_overrides(self.parameters, overrides)
        self.reset_parameter_caches()

    def _rebuild(self, raw: ParameterNode, statutory: bool) -> None:
        assignments = self.dated_assignments
        if not assignments:
            self.parameters, self.projected_timelines = process_parameter_tree(raw)
            return
        unreformed = raw.clone()
        projected = prior_law_projection(assignments, unreformed, statutory)
        for assignment in assignments:
            write_assignment(raw.get_child(assignment.path), assignment, projected)
        self.parameters, self.projected_timelines = process_parameter_tree(
            raw, unreformed
        )

    def _apply_legacy_overrides(self) -> None:
        if self.legacy_overrides:
            apply_legacy_overrides(self.parameters, self.legacy_overrides)

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

        # Dated reform changes on the statutory timeline, and legacy
        # overrides of the annualised parameters, that every rebuild of the
        # parameters applies again. Replaced, never appended to in place, so a
        # cloned system does not share later additions.
        self.dated_assignments: List[ParameterAssignment] = []
        self.legacy_overrides: List[LegacyOverride] = []

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
            # A copy: these timelines are prior law for every later reform,
            # and the lists just captured belong to this system's own tree.
            _projected_timelines_cache = copy_timelines(self.projected_timelines)


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


# Fixed-point passes for prior law's projection; dependencies between the
# changes that need it (a frozen allowance and an aligned NICs threshold, say)
# settle in two.
PRIOR_LAW_PASSES = 4


def _same_timelines(a: Dict[str, Timeline], b: Dict[str, Timeline]) -> bool:
    def key(timeline):
        return [(entry.instant_str, entry.value) for entry in timeline or []]

    return a.keys() == b.keys() and all(key(a[name]) == key(b[name]) for name in a)


def prior_law_projection(
    assignments: List[ParameterAssignment],
    unreformed: ParameterNode,
    statutory: bool = True,
) -> Callable[[str], Optional[Timeline]]:
    """Prior law's projected timeline, by parameter name, for a reform.

    Where a change reaches the part of a parameter's timeline that
    projection fills (see ``requires_projection``), prior law there is the
    path that parameter takes with every other change in the reform but
    without its own. Each such parameter is projected with the others'
    changes, which are written with the previous pass's projections, until
    the projections stop changing. ``unreformed`` is the tree the changes are
    written onto; ``statutory`` says it is the YAML as loaded, whose
    projection without changes is cached.
    """
    needing = sorted(
        {
            assignment.path
            for assignment in assignments
            if requires_projection(unreformed.get_child(assignment.path), assignment)
        }
    )
    if not needing:
        return lambda name: None
    start = (
        projected_timelines()
        if statutory
        else process_parameter_tree(unreformed.clone(), annualise=False)[1]
    )
    environment = {path: start.get(path) for path in needing}

    def lookup(name: str) -> Optional[Timeline]:
        found = environment.get(name)
        return found if found is not None else start.get(name)

    for _ in range(PRIOR_LAW_PASSES):
        updated = {}
        for path in needing:
            tree = unreformed.clone()
            for assignment in assignments:
                if assignment.path != path:
                    write_assignment(
                        tree.get_child(assignment.path), assignment, lookup
                    )
            updated[path] = process_parameter_tree(tree, annualise=False)[1].get(path)
        if _same_timelines(updated, environment):
            break
        environment = updated
    else:
        logger.warning(
            "Prior law's projection for %s did not settle in %d passes.",
            ", ".join(needing),
            PRIOR_LAW_PASSES,
        )
    return lookup


# Recently rebuilt parameters, by their dated changes, so simulations of the
# same reform (one per year or region, say) skip the rebuild. Entries are
# cloned on the way in and out and never changed.
_REBUILT_CACHE_SIZE = 4
_rebuilt_parameters_cache: "OrderedDict[tuple, Tuple[ParameterNode, Dict[str, Timeline]]]" = OrderedDict()


def _assignments_key(assignments: List[ParameterAssignment]) -> tuple:
    return tuple(
        (a.path, str(a.start), str(a.stop), repr(a.value), a.order) for a in assignments
    )


def _remember_rebuilt(
    key: tuple, parameters: ParameterNode, projected: Dict[str, Timeline]
) -> None:
    _rebuilt_parameters_cache[key] = (parameters, projected)
    _rebuilt_parameters_cache.move_to_end(key)
    while len(_rebuilt_parameters_cache) > _REBUILT_CACHE_SIZE:
        _rebuilt_parameters_cache.popitem(last=False)


# Create system instance for module-level access
system = CountryTaxBenefitSystem()
parameters = system.parameters
variables = system.variables
