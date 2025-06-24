import copy

import streamlit as st

from data_pipelines.delta_table import populate_latest_dcs_constraints
from database import (load_latest_constraints,
                      save_optimizer_last_run_constraints,
                      save_constraints,
                      save_allocation_data, load_optimizer_last_run_constraints)
from optimizer.optimizer import solve_h2_optimizer
from params import *


def check_header_pressure():
    """
    Calls the data fetching script and gets header pressure checks and passes the dcs_constraints
    """
    dcs_constraints, current_flow = populate_latest_dcs_constraints()
    header_pressure = dcs_constraints['header_pressure']
    print(f'Header Pressure - {header_pressure}')
    return header_pressure > 125, dcs_constraints, current_flow


def trigger_optimizer_if_needed(manual_trigger=False):
    """
    Checks conditions and triggers the optimizer.
    Conditions:
    1. Latest constraints are different from the last run.
    2. Header pressure is above X.
    3. User clicks the 'Run Optimizer' button.
    """
    print("Log: In Optimizer Trigger")
    should_run_optimizer = False
    optimizer_trigger_reason = []
    ROLE_CONSTRAINTS = get_constraints()
    # Condition 1: Check for constraint changes
    # Compare current constraints with the last saved constraints for optimizer run
    current_all_constraints_snapshot = {}
    for role_name in ROLES:
        if role_name in ROLE_CONSTRAINTS:
            # Load the latest constraints for this role from the DB for comparison
            latest_db_constraints_for_role = load_latest_constraints(role_name, ROLE_CONSTRAINTS[role_name])
            current_all_constraints_snapshot[role_name] = copy.deepcopy(latest_db_constraints_for_role)

    if current_all_constraints_snapshot != st.session_state.last_run_constraints:
        should_run_optimizer = True
        optimizer_trigger_reason.append("Constraint changes detected.")
        print("Constraint changes detected.")

    # Condition 2: Check header pressure
    header_pressure_check, dcs_constraints, current_flow = check_header_pressure()
    if header_pressure_check:
        should_run_optimizer = True
        optimizer_trigger_reason.append("Header pressure condition met.")
        print("Header pressure condition met.")

    # Condition 3: Manual trigger
    if manual_trigger or st.session_state.run_optimizer_button_clicked:
        should_run_optimizer = True
        optimizer_trigger_reason.append("Manual 'Run Optimizer' button clicked.")
        st.session_state.run_optimizer_button_clicked = False  # Reset button flag
        print("Manual button clicked.")

    if should_run_optimizer:
        st.info(f"Triggering optimizer due to: {', '.join(optimizer_trigger_reason)}")
        new_recommendations = generate_hydrogen_recommendations(dcs_constraints, current_flow)
        st.session_state.dashboard_data = new_recommendations
        # Update last_run_constraints AFTER optimizer runs and BEFORE saving
        st.session_state.last_run_constraints = copy.deepcopy(current_all_constraints_snapshot)
        save_optimizer_last_run_constraints(st.session_state.last_run_constraints)
        st.success("Optimizer run completed! Dashboard updated.")
        save_allocation_data(st.session_state.dashboard_data)
        # st.rerun()
    else:
        # print("Optimizer conditions not met. Not running.") # For debugging
        pass  # Optimizer not triggered


def get_final_constraint_values(constraints, dcs_constraints=dcs_constraints_dummy):
    final_constraints = {
        'pipeline': {'min': dcs_constraints['pipeline_flow'], 'max': dcs_constraints['pipeline_flow']},

        'hcl': {
            'min': dcs_constraints['hcl_production'] * constraints['Caustic Plant']['H2 required (NM3) per ton of HCl'],
            'max': dcs_constraints['hcl_production'] * constraints['Caustic Plant'][
                'H2 required (NM3) per ton of HCl']},

        'bank': {'min': 0, 'max': dcs_constraints['bank_available']},

        'h2o2': {'min': constraints['H2O2 Plant']['H2O2 Production Capacity (TPH)']['min'] * constraints['H2O2 Plant'][
            'H2 (NM3) required per ton of H2O2'],
                 'max': dcs_constraints['h2o2_production'] * constraints['H2O2 Plant'][
                     'H2 (NM3) required per ton of H2O2']},

        'flaker-1': {'min': dcs_constraints['flaker-1_load'] * constraints['Flaker Plant'][
            'Flaker-1 H2 Specific Consumption (NM3/Ton)'],
                     'max': dcs_constraints['flaker-1_load'] * constraints['Flaker Plant'][
                         'Flaker-1 H2 Specific Consumption (NM3/Ton)']},

        'flaker-2': {'min': dcs_constraints['flaker-2_load'] * constraints['Flaker Plant'][
            'Flaker-2 H2 Specific Consumption (NM3/Ton)'],
                     'max': dcs_constraints['flaker-2_load'] * constraints['Flaker Plant'][
                         'Flaker-2 H2 Specific Consumption (NM3/Ton)']},

        'flaker-3': {'min': 750,
                     'max': dcs_constraints['flaker-3_load'] * constraints['Flaker Plant'][
                         'Flaker-3 H2 Specific Consumption (NM3/Ton)']},

        'flaker-4': {'min': 750,
                     'max': dcs_constraints['flaker-4_load'] * constraints['Flaker Plant'][
                         'Flaker-4 H2 Specific Consumption (NM3/Ton)']},

        'boiler_p60': {
            'min': constraints['Power Plant']['P60 - H2 capacity']['min'] * dcs_constraints['boiler_p60_run'],
            'max': constraints['Power Plant']['P60 - H2 capacity']['max'] * dcs_constraints['boiler_p60_run']},

        'boiler_p120': {
            'min': constraints['Power Plant']['P120 - H2 capacity']['min'] * dcs_constraints['boiler_p120_run'],
            'max': constraints['Power Plant']['P120 - H2 capacity']['max'] * dcs_constraints['boiler_p120_run']},

        'vent': {'min': 0,
                 'max': dcs_constraints['caustic_production'] * constraints['Caustic Plant'][
                     'H2 generated (NM3) per ton of caustic']},
    }

    prices = constraints['Finance']
    return final_constraints, prices


def generate_hydrogen_recommendations(dcs_constraints, current_flow):
    """
    Reads the latest constraints from the database for all roles
    and generates dummy hydrogen allocation recommendations.

    The actual optimization logic should be implemented in this function.
    For now, it generates random recommendations based on initial allocated values.

    Returns:
        dict: A dictionary of hydrogen allocation data with updated 'recommended' values.
    """
    ROLE_CONSTRAINTS = get_constraints()
    all_latest_constraints = {}
    for role in ROLES:
        # Load constraints only for roles that have them defined
        if role in ROLE_CONSTRAINTS:
            constraints_schema = ROLE_CONSTRAINTS[role]
            latest_role_constraints = load_latest_constraints(role, constraints_schema)
            all_latest_constraints[role] = latest_role_constraints
            # print(f"Loaded latest constraints for {role}: {latest_role_constraints}")
        else:
            print(f"No specific constraints defined for role: {role}")

    # --- Optimization Logic ---

    if 'Caustic Plant' in all_latest_constraints and 'Duration of pipeline demand change (hrs)' in \
            all_latest_constraints['Caustic Plant']:
        duration = all_latest_constraints['Caustic Plant']['Duration of pipeline demand change (hrs)']
    else:
        # Default duration or handle error if constraint is not found.
        duration = 0.5
        st.warning("Duration constraint for Caustic Plant not found. Using default duration of 30 min.")

    final_constraints, prices = get_final_constraint_values(all_latest_constraints, dcs_constraints)
    solution = solve_h2_optimizer(duration, final_constraints, prices, all_latest_constraints)

    allocation_details = HYDROGEN_ALLOCATION_DATA

    if solution and solution.get("status") == "optimal":
        for display_name, internal_key in key_mapping.items():
            if internal_key in solution['allocation_details']:
                details = solution['allocation_details'][internal_key]

                if display_name in allocation_details:
                    allocation_details[display_name]["allocated"] = current_flow[internal_key]
                    allocation_details[display_name]["recommended"] = details["amount"]
                    allocation_details[display_name]["status"] = "pending"  # Reset status to pending for new recs
                    allocation_details[display_name]["comment"] = ""  # Clear comments
                    allocation_details[display_name]["min_constrained"] = final_constraints[internal_key]['min']
                    allocation_details[display_name]["max_constrained"] = final_constraints[internal_key]['max']
                else:
                    print(
                        f"Warning: Display name '{display_name}' "
                        f"from key_mapping not found in HYDROGEN_ALLOCATION_DATA.")
            else:
                print(
                    f"Warning: Internal key '{internal_key}' "
                    f"not found in optimizer allocation details for display name '{display_name}'.")
    else:
        st.error(f"Optimizer failed or returned an infeasible solution: {solution.get('message', 'Unknown error')}")
        # Reset recommendations to the current H2 flow as per DCS, if optimizer fails.
        for area in allocation_details:
            allocation_details[area]["allocated"] = current_flow[key_mapping.get(area)]
            allocation_details[area]["recommended"] = allocation_details[area][
                "allocated"]  # Keep current allocated as recommended
            allocation_details[area]["status"] = "pending"
            allocation_details[area]["comment"] = "Optimizer failed to provide new recommendations. \
            Current flow assigned."

    current_recommendations = copy.deepcopy(allocation_details)

    return current_recommendations


def last_run_constraints_trigger_run():
    st.session_state.last_run_constraints = load_optimizer_last_run_constraints()


def initial_db_trigger():
    st.session_state.initial_db_setup_done = True
    ROLE_CONSTRAINTS = get_constraints()
    # Check if the optimizer_state table is empty (indicates truly first run)
    initial_optimizer_state = load_optimizer_last_run_constraints()
    if not initial_optimizer_state:
        st.info("First startup detected. Initializing default constraints and running optimizer...")

        # Seed predefined initial constraints into the database for each role
        for role_name, constraints_data in entry_constraints_dummy.items():
            if role_name in ROLE_CONSTRAINTS and ROLE_CONSTRAINTS[role_name]:
                save_constraints(role_name, constraints_data, ROLE_CONSTRAINTS[role_name])

        # After seeding, load them into session state for the optimizer to use
        initial_constraints_snapshot = {}
        for role_name in ROLES:
            if role_name in ROLE_CONSTRAINTS:  # Only roles with defined constraints are relevant
                initial_constraints_snapshot[role_name] = load_latest_constraints(role_name,
                                                                                  ROLE_CONSTRAINTS[role_name])

        # Run optimizer for the very first time
        dcs_constraints, current_flow = populate_latest_dcs_constraints()
        new_recommendations = generate_hydrogen_recommendations(dcs_constraints, current_flow)
        st.session_state.dashboard_data = new_recommendations

        # Save the initial optimizer state and recommendations to DB
        st.session_state.last_run_constraints = copy.deepcopy(initial_constraints_snapshot)
        save_optimizer_last_run_constraints(st.session_state.last_run_constraints)
        save_allocation_data(st.session_state.dashboard_data)  # Save initial recommendations to the allocations table

        st.success("Initial optimizer run completed and database seeded with default constraints!")
