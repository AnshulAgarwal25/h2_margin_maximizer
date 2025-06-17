from pyomo.environ import *
from pyomo.opt import SolverFactory

from params import *


def build_h2_optimizer(total_h2_generated, duration, final_constraints, prices):
    """
    Builds a Pyomo optimization model for hydrogen allocation.

    Args:
        total_h2_generated (float): The total amount of H2 available for allocation.
        duration (int): The duration in days, used to determine H2O2 allocation priority.
        final_constraints (dict): Final min and max for allocation areas
        prices (dict): Contribution margin for all allocation areas

    Returns:
        pyomo.environ.ConcreteModel: The constructed Pyomo model.
    """
    model = ConcreteModel()

    dummy_constraints = final_constraints
    contribution_margin_base = prices

    allocation_to_margin_category = {
        'pipeline': 'Pipeline',
        'hcl': 'HCl',
        'bank': 'Bank',
        'h2o2': 'H2O2',
        'flaker-1': 'Flaker',
        'flaker-2': 'Flaker',
        'flaker-3': 'Flaker',
        'flaker-4': 'Flaker',
        'boiler_p60': 'Boiler',
        'boiler_p120': 'Boiler',
        'vent': 'Vent'
    }

    # Determine effective contribution margins, applying priority for H2O2 if duration > 7
    effective_contribution_margin = contribution_margin_base.copy()
    if duration > 7:
        effective_contribution_margin['H2O2'] += 1_000_000  # A large number to ensure priority

    # --- 2. Model Sets and Parameters ---
    model.ALLOCATION_POINTS = Set(initialize=dummy_constraints.keys())
    model.min_h2_limit = Param(model.ALLOCATION_POINTS, initialize={k: v['min'] for k, v in dummy_constraints.items()})
    model.max_h2_limit = Param(model.ALLOCATION_POINTS, initialize={k: v['max'] for k, v in dummy_constraints.items()})

    def _get_margin(model, point):
        """Helper function to get the margin based on the allocation category."""
        category = allocation_to_margin_category[point]
        return effective_contribution_margin[category]

    model.margin = Param(model.ALLOCATION_POINTS, initialize=_get_margin)

    # --- 3. Decision Variables ---
    # Binary variable: `allocate[p]` is 1 if H2 is allocated to point `p`, 0 otherwise.
    model.allocate = Var(model.ALLOCATION_POINTS, domain=Binary)
    # Continuous variable: `h2_amount[p]` is the actual amount of H2 allocated to point `p`.
    model.h2_amount = Var(model.ALLOCATION_POINTS, domain=NonNegativeReals)

    # --- 4. Objective Function ---
    def objective_rule(model):
        return sum(model.h2_amount[p] * model.margin[p] for p in model.ALLOCATION_POINTS)

    model.objective = Objective(rule=objective_rule, sense=maximize)

    # --- 5. Constraints ---

    # Constraint 1: Total H2 allocated must not exceed the total available H2.
    def total_h2_constraint_rule(model):
        return sum(model.h2_amount[p] for p in model.ALLOCATION_POINTS) <= total_h2_generated

    model.total_h2_constraint = Constraint(rule=total_h2_constraint_rule)

    # Constraint 2: Link `h2_amount` to `allocate` and enforce min/max bounds.
    # If `allocate[p]` is 0, then `h2_amount[p]` must be 0.
    # If `allocate[p]` is 1, then `h2_amount[p]` must be within its specified min and max limits.

    # Minimum H2 allocation constraint: `h2_amount[p] >= min_h2_limit[p] * allocate[p]`
    # If allocate[p] is 0, h2_amount[p] >= 0 (always true for NonNegativeReals)
    # If allocate[p] is 1, h2_amount[p] >= min_h2_limit[p]
    def min_h2_allocation_rule(model, p):
        return model.h2_amount[p] >= model.min_h2_limit[p] * model.allocate[p]

    model.min_h2_allocation = Constraint(model.ALLOCATION_POINTS, rule=min_h2_allocation_rule)

    # Maximum H2 allocation constraint: `h2_amount[p] <= max_h2_limit[p] * allocate[p]`
    # If allocate[p] is 0, h2_amount[p] <= 0, forcing h2_amount[p] to be 0 (since it's NonNegative)
    # If allocate[p] is 1, h2_amount[p] <= max_h2_limit[p]
    def max_h2_allocation_rule(model, p):
        return model.h2_amount[p] <= model.max_h2_limit[p] * model.allocate[p]

    model.max_h2_allocation = Constraint(model.ALLOCATION_POINTS, rule=max_h2_allocation_rule)

    # Constraint 3: Mandatory allocations for 'pipeline', 'hcl', and 'h2o2'.
    # These points must always be selected for allocation (`allocate[p]` must be 1).
    mandatory_points = ['pipeline', 'hcl', 'h2o2']

    def mandatory_allocation_rule(model, p):
        if p in mandatory_points:
            return model.allocate[p] == 1
        return Constraint.Skip  # Skip this constraint for non-mandatory points

    model.mandatory_allocation = Constraint(model.ALLOCATION_POINTS, rule=mandatory_allocation_rule)

    model.dual = Suffix(direction=Suffix.IMPORT)

    return model


def solve_h2_optimizer(duration, final_constraints, prices,
                       entry_constraints,
                       dcs_constraints=dcs_constraints_dummy):
    """
    Builds and solves the H2 allocation optimization model.

    Args:
        duration (int): The duration in days.
        final_constraints (dict): Final min and max for allocation areas
        prices (dict): Contribution margin for all allocation areas
        entry_constraints (dict): entry constraints loaded from last entry
        dcs_constraints (dict): constraints from DCS

    Returns:
        dict: A dictionary containing the optimization results (objective value,
              allocated amounts, and allocation decisions) or an error message.
    """
    total_h2_generated = (dcs_constraints['caustic_production'] *
                          entry_constraints['Caustic Plant']['H2 generated (NM3) per ton of caustic'])
    model = build_h2_optimizer(total_h2_generated, duration, final_constraints, prices)

    # Initialize the CBC solver. Ensure 'cbc' is installed and accessible in your system's PATH.
    # If you have another solver (e.g., GLPK), you can specify it here: SolverFactory('glpk')
    solver = SolverFactory('glpk')
    results = solver.solve(model, tee=True)

    # Process and print the results based on the solver's status
    if (results.solver.status == SolverStatus.ok) and \
            (results.solver.termination_condition == TerminationCondition.optimal):
        print("\n--- Optimization Results ---")
        print(f"Total H2 Generated: {total_h2_generated:.2f} units")
        print(f"Duration: {duration} days")
        print(f"Maximized Contribution Margin: {model.objective():.2f}")
        print("\nH2 Allocation Details:")

        allocated_total_h2 = 0
        allocation_details = {}
        for p in model.ALLOCATION_POINTS:
            # Check if the binary allocation variable is effectively 1 (due to floating point precision)
            alloc_val = model.allocate[p].value
            h2_val = model.h2_amount[p].value

            is_allocated = bool(round(alloc_val)) if alloc_val is not None else False
            allocated_amount = h2_val if h2_val is not None else 0.0

            allocation_details[p] = {
                'allocated': is_allocated,
                'amount': allocated_amount,
                'margin_per_unit': model.margin[p]
            }

            print(f"  {p:<12}: Allocated = {'YES' if is_allocated else 'NO'}, "
                  f"Amount = {allocated_amount:.2f} units, "
                  f"Margin = {model.margin[p]:.2f}")

            allocated_total_h2 += allocated_amount

        print(f"\nTotal H2 Actually Allocated: {allocated_total_h2:.2f} units")
        # analyze_limiting_constraints(model, total_h2_generated)

        return {
            "status": "optimal",
            "objective_value": model.objective(),
            "total_h2_allocated": allocated_total_h2,
            "allocation_details": allocation_details
        }
    elif results.solver.termination_condition == TerminationCondition.infeasible:
        print("\n--- Optimization Failed ---")
        print("The problem is infeasible. No solution satisfies all constraints with the given H2 generation.")
        return {"status": "infeasible", "message": "The problem is infeasible."}
    else:
        print("\n--- Optimization Failed ---")
        print(f"Solver Status: {results.solver.status}")
        print(f"Termination Condition: {results.solver.termination_condition}")
        return {"status": "error",
                "message": f"Solver failed with status: {results.solver.status}, termination: {results.solver.termination_condition}"}
