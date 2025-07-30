import streamlit as st
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

    # Determine effective contribution margins, applying priority for H2O2 if duration > 3
    effective_contribution_margin = contribution_margin_base.copy()

    if 'H2O2 Plant' in st.session_state.constraint_values.keys():
        duration_threshold = \
            st.session_state.constraint_values['H2O2 Plant']['Load increase/decrease time for H2O2 (hrs)']
    elif 'H2O2 Plant' in st.session_state.last_run_constraints.keys():
        duration_threshold = \
            st.session_state.last_run_constraints['H2O2 Plant']['Load increase/decrease time for H2O2 (hrs)']
    else:
        duration_threshold = 8

    if duration > duration_threshold:
        effective_contribution_margin['H2O2'] += 1_000_000  # A large number to ensure priority

    # --- 1. Model Sets and Parameters ---
    model.ALLOCATION_POINTS = Set(initialize=dummy_constraints.keys())
    model.min_h2_limit = Param(model.ALLOCATION_POINTS, initialize={k: v['min'] for k, v in dummy_constraints.items()})
    model.max_h2_limit = Param(model.ALLOCATION_POINTS, initialize={k: v['max'] for k, v in dummy_constraints.items()})

    def _get_margin(model, point):
        category = allocation_to_margin_category[point]
        if point == 'boiler_p60':
            return effective_contribution_margin[category] + 0.01
        return effective_contribution_margin[category]

    model.margin = Param(model.ALLOCATION_POINTS, initialize=_get_margin)

    # --- 2. Decision Variables ---
    model.allocate = Var(model.ALLOCATION_POINTS, domain=Binary)
    model.h2_amount = Var(model.ALLOCATION_POINTS, domain=NonNegativeReals)

    # --- 3. Objective Function ---
    def objective_rule(model):
        return sum(model.h2_amount[p] * model.margin[p] for p in model.ALLOCATION_POINTS)

    model.objective = Objective(rule=objective_rule, sense=maximize)

    # --- 4. Constraints ---
    def total_h2_constraint_rule(model):
        return sum(model.h2_amount[p] for p in model.ALLOCATION_POINTS) <= total_h2_generated

    model.total_h2_constraint = Constraint(rule=total_h2_constraint_rule)

    # Ensure bank is allocated in multiples of 440
    if 'bank' in dummy_constraints:
        model.bank_units = Var(domain=NonNegativeIntegers)

        def bank_allocation_multiple_rule(model):
            return model.h2_amount['bank'] == 440 * model.bank_units

        model.bank_allocation_multiple = Constraint(rule=bank_allocation_multiple_rule)

    def min_h2_allocation_rule(model, p):
        return model.h2_amount[p] >= model.min_h2_limit[p] * model.allocate[p]

    model.min_h2_allocation = Constraint(model.ALLOCATION_POINTS, rule=min_h2_allocation_rule)

    def max_h2_allocation_rule(model, p):
        return model.h2_amount[p] <= model.max_h2_limit[p] * model.allocate[p]

    model.max_h2_allocation = Constraint(model.ALLOCATION_POINTS, rule=max_h2_allocation_rule)

    mandatory_points = ['pipeline', 'hcl', 'h2o2', 'flaker-1', 'flaker-2']
    if final_constraints['flaker-3']['min'] > 750:
        mandatory_points.append('flaker-3')

    if final_constraints['flaker-4']['min'] > 750:
        mandatory_points.append('flaker-4')

    def mandatory_allocation_rule(model, p):
        if p in mandatory_points:
            return model.allocate[p] == 1
        return Constraint.Skip

    model.mandatory_allocation = Constraint(model.ALLOCATION_POINTS, rule=mandatory_allocation_rule)

    # --- 5. Special Disjunctive Constraint for flaker-3 and flaker-4 ---
    BIG_M = 10_000
    offset = 400 * (220 / 67)

    model.flaker_range_mode = Var(['flaker-3'], domain=Binary)

    model.flaker_restricted_upper = ConstraintList()
    model.flaker_exact_max_lower = ConstraintList()
    model.flaker_exact_max_upper = ConstraintList()

    for p in ['flaker-3']:
        max_val = dummy_constraints[p]['max']

        # Range mode (0): h2_amount ≤ max - offset (or 0 if max < offset)
        capped_upper = max(0, max_val - offset)
        model.flaker_restricted_upper.add(
            model.h2_amount[p] <= capped_upper + (BIG_M * model.flaker_range_mode[p])
        )

        # If range_mode = 0: x >= 0 (already ensured by NonNegativeReals domain)

        # Max mode (1): h2_amount == max_val
        model.flaker_exact_max_lower.add(
            model.h2_amount[p] >= max_val - BIG_M * (1 - model.flaker_range_mode[p])
        )
        model.flaker_exact_max_upper.add(
            model.h2_amount[p] <= max_val + BIG_M * (1 - model.flaker_range_mode[p])
        )

        if max_val == 0:
            @model.Constraint()
            def flaker_mode_fixed(m):
                return m.flaker_range_mode[p] == 0

    # # --- 6. Dual variables for sensitivity analysis (optional) ---
    # model.dual = Suffix(direction=Suffix.IMPORT)

    return model


def flaker_mismatch_handling(p, allocation_amount, dcs_constraints):
    """
    Matching flaker allocation to actual flows if within 2% of the difference with actual

    :param p: allocation point name
    :param allocation_amount: actual value allocated
    :param dcs_constraints: also contains flaker 3 and 4 current flow
    :return: new allocated amount
    """
    new_allocation_amount = allocation_amount

    # Define tolerance check mapping
    flaker_targets = {
        'flaker-3': 'flaker-3_h2_flow',
        'flaker-4': 'flaker-4_h2_flow'
    }

    if p in flaker_targets:
        target_flow = dcs_constraints[flaker_targets[p]]
        if abs(allocation_amount - target_flow) <= 0.02 * target_flow:
            new_allocation_amount = target_flow

    return new_allocation_amount


def solve_h2_optimizer(duration, final_constraints, prices,
                       current_flow,
                       dcs_constraints=dcs_constraints_dummy):
    """
    Builds and solves the H2 allocation optimization model.

    Args:
        duration (int): The duration of days.
        final_constraints (dict): Final min and max for allocation areas
        prices (dict): Contribution margin for all allocation areas
        current_flow (dict): current flows
        dcs_constraints (dict): constraints from DCS

    Returns:
        dict: A dictionary containing the optimization results (objective value,
              allocated amounts, and allocation decisions) or an error message.
    """
    total_h2_generated = round((dcs_constraints['caustic_production'] *
                                dcs_constraints['caustic_production_norm']), 2)
    print(f"H2 Generated as per load and consumption norm: {total_h2_generated}")

    total_flow_excluding_vent = sum(
        value for key, value in current_flow.items() if key not in ["vent", "ech_flow"]
    )

    print(f"H2 Consumed as per current flow: {total_flow_excluding_vent}")
    if total_h2_generated < total_flow_excluding_vent:
        total_h2_generated = total_flow_excluding_vent

    # total_h2_generated = max(total_h2_generated, dcs_constraints['caustic_production'] * 280)
    model = build_h2_optimizer(total_h2_generated, duration, final_constraints, prices)

    # Initialize the CBC solver. Ensure 'cbc' is installed and accessible in your system's PATH.
    # If you have another solver (e.g., GLPK), you can specify it here: SolverFactory('glpk')
    solver = SolverFactory('glpk')

    # interim writing of model files if required for debug
    # model.write('model_debug.lp', io_options={'symbolic_solver_labels': True})
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

            if p in ['flaker-3', 'flaker-4']:
                allocated_amount = flaker_mismatch_handling(p, allocated_amount, dcs_constraints)

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
