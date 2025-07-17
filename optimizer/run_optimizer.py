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
    st.sidebar.write(f"Header Pressure: {header_pressure}")

    if 'H2 Plant' in st.session_state.constraint_values.keys():
        header_pressure_threshold = \
            st.session_state.constraint_values['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max']
    elif 'H2 Plant' in st.session_state.last_run_constraints:
        header_pressure_threshold = \
            st.session_state.last_run_constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max']
    else:
        header_pressure_threshold = 135
    return header_pressure > header_pressure_threshold, dcs_constraints, current_flow


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

        st.sidebar.write(f"Caustic Production: {round(dcs_constraints['caustic_production'], 2)} TPH")

        if 'Caustic Plant' in st.session_state.constraint_values.keys():
            h2_generation = st.session_state.constraint_values['Caustic Plant']['H2 generated (NM3) per ton of caustic']
        else:
            h2_generation = st.session_state.last_run_constraints['Caustic Plant'][
                'H2 generated (NM3) per ton of caustic']

        st.sidebar.write(f"H2 Generated: {round(dcs_constraints['caustic_production'], 2) * h2_generation} NM3/hr")

        st.session_state.dashboard_data = new_recommendations
        # Update last_run_constraints AFTER optimizer runs and BEFORE saving
        st.session_state.last_run_constraints = copy.deepcopy(current_all_constraints_snapshot)
        save_optimizer_last_run_constraints(st.session_state.last_run_constraints)
        st.success("Optimizer run completed! Dashboard updated.")
        save_allocation_data(st.session_state.dashboard_data)
        st.session_state.current_page = "dashboard"
    else:
        pass  # Optimizer not triggered


def get_final_constraint_values(constraints, dcs_constraints=dcs_constraints_dummy):
    for flaker in ['flaker-1_h2_flow', 'flaker-2_h2_flow']:
        if dcs_constraints[flaker] <= 10:
            dcs_constraints[flaker] = 0

    final_constraints = {
        'pipeline': {'min': dcs_constraints['pipeline_flow'], 'max': dcs_constraints['pipeline_flow']},

        'hcl': {
            'min': dcs_constraints['hcl_h2_flow'],
            'max': dcs_constraints['hcl_h2_flow'],
        },

        'bank': {'min': 0, 'max': dcs_constraints['bank_available']},

        'h2o2': {'min': max((constraints['H2O2 Plant']['H2O2 Production Capacity (TPD)']['min'] / 24) *
                            constraints['H2O2 Plant']['H2 (NM3) required per ton of H2O2'],

                            dcs_constraints['h2o2_h2_flow']),
                 'max': min(dcs_constraints['h2o2_h2_flow'],

                            (constraints['Marketing']['Demand - H2O2 (TPD)']['max'] / 24) *
                            constraints['H2O2 Plant']['H2 (NM3) required per ton of H2O2'])},

        'flaker-1': {'min': dcs_constraints['flaker-1_h2_flow'], 'max': dcs_constraints['flaker-1_h2_flow']},
        'flaker-2': {'min': dcs_constraints['flaker-2_h2_flow'], 'max': dcs_constraints['flaker-2_h2_flow']},

        'flaker-3': {'min': 750,
                     'max': min(dcs_constraints['flaker-3_load'] *
                                constraints['Flaker Plant']['Flaker-3 H2 Specific Consumption (NM3/Ton)'],

                                dcs_constraints['850tpd_caustic'] *
                                constraints['Caustic Plant']['H2 generated (NM3) per ton of caustic']) - 1000},

        'flaker-4': {'min': 750,
                     'max': min(dcs_constraints['flaker-4_load'] *
                                constraints['Flaker Plant']['Flaker-4 H2 Specific Consumption (NM3/Ton)'],

                                dcs_constraints['850tpd_caustic'] *
                                constraints['Caustic Plant']['H2 generated (NM3) per ton of caustic'])},

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

    # cleaning for dcs readings
    for key, bounds in final_constraints.items():
        bounds['min'] = max(bounds['min'], 0)
    bounds['max'] = max(bounds['max'], 0)

    # doing this to de-prioritize bank filling when header pressure in control
    if dcs_constraints['header_pressure'] < constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max']:
        prices['Bank'] = 0

    # getting h2o2 min to min production possible when duration change condition is met and \
    # header pressure breach is observed
    if (dcs_constraints['header_pressure'] >= constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max'] and
            dcs_constraints['pipeline_disruption_hrs'] >= constraints['H2O2 Plant'][
                'Load increase/decrease time for H2O2 (hrs)']):
        final_constraints['h2o2']['max'] = min(
            (constraints['H2O2 Plant']['H2O2 Production Capacity (TPD)']['max'] / 24) *
            constraints['H2O2 Plant']['H2 (NM3) required per ton of H2O2'],

            (constraints['Marketing']['Demand - H2O2 (TPD)']['max'] / 24) *
            constraints['H2O2 Plant']['H2 (NM3) required per ton of H2O2'])

    # getting h2o2 min to min production possible when duration change condition is met and \
    # header pressure breach is observed
    if (dcs_constraints['header_pressure'] <= constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)'][
        'min'] and
            dcs_constraints['pipeline_disruption_hrs'] >= constraints['H2O2 Plant'][
                'Load increase/decrease time for H2O2 (hrs)']):
        final_constraints['h2o2']['min'] = (constraints['H2O2 Plant']['H2O2 Production Capacity (TPD)']['min'] / 24) * \
                                           constraints['H2O2 Plant']['H2 (NM3) required per ton of H2O2']

    # flaker 3 and 4 current flow matching
    final_constraints['flaker-3']['max'] = max(final_constraints['flaker-3']['max'],
                                               dcs_constraints['flaker-3_h2_flow'])

    final_constraints['flaker-4']['max'] = max(final_constraints['flaker-4']['max'],
                                               dcs_constraints['flaker-4_h2_flow'])

    # if duration < 1hr, then cant change flaker 3 & 4 flow
    if (dcs_constraints['header_pressure'] >= constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max'] and
            dcs_constraints['pipeline_disruption_hrs'] < constraints['Flaker Plant'][
                'Flaker - Changeover time (NG to mix) (hrs)']):
        final_constraints['flaker-3']['min'] = dcs_constraints['flaker-3_h2_flow']
        final_constraints['flaker-3']['max'] = dcs_constraints['flaker-3_h2_flow']

        final_constraints['flaker-4']['min'] = dcs_constraints['flaker-4_h2_flow']
        final_constraints['flaker-4']['max'] = dcs_constraints['flaker-4_h2_flow']

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
    st.session_state.bank_filling_status = dcs_constraints["is_bank_on"] > 0

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

    if 'pipeline_disruption_hrs' in dcs_constraints:
        duration = dcs_constraints['pipeline_disruption_hrs']
    else:
        # Default duration or handle error if constraint is not found.
        duration = 0.5
        st.warning("Duration constraint for Caustic Plant not found. Using default duration of 30 min.")

    final_constraints, prices = get_final_constraint_values(all_latest_constraints, dcs_constraints)
    solution = solve_h2_optimizer(duration, final_constraints, prices, all_latest_constraints, dcs_constraints)

    allocation_details = HYDROGEN_ALLOCATION_DATA

    if solution and solution.get("status") == "optimal":
        for display_name, internal_key in key_mapping.items():
            if internal_key in solution['allocation_details']:
                details = solution['allocation_details'][internal_key]

                if display_name in allocation_details:
                    allocation_details[display_name]["allocated"] = current_flow[internal_key]
                    allocation_details[display_name]["recommended"] = details["amount"]
                    allocation_details[display_name]["status"] = "accepted"  # Reset status to pending for new recs
                    allocation_details[display_name]["comment"] = ""  # Clear comments
                    allocation_details[display_name]["min_constrained"] = final_constraints[internal_key]['min']
                    allocation_details[display_name]["max_constrained"] = final_constraints[internal_key]['max']
                    allocation_details[display_name]['margin_per_unit'] = details['margin_per_unit']
                else:
                    print(
                        f"Warning: Display name '{display_name}' "
                        f"from key_mapping not found in HYDROGEN_ALLOCATION_DATA.")
            else:
                print(
                    f"Warning: Internal key '{internal_key}' "
                    f"not found in optimizer allocation details for display name '{display_name}'.")
    else:
        # st.error(f"Optimizer failed or returned an infeasible solution: {solution.get('message', 'Unknown error')}")
        # Reset recommendations to the current H2 flow as per DCS, if optimizer fails.
        for area in allocation_details:
            allocation_details[area]["allocated"] = current_flow[key_mapping.get(area)]
            allocation_details[area]["recommended"] = allocation_details[area][
                "allocated"]  # Keep current allocated as recommended
            allocation_details[area]["status"] = "accepted"
            allocation_details[area]["comment"] = "."
            allocation_details[area]["min_constrained"] = final_constraints[key_mapping.get(area)]['min']
            allocation_details[area]["max_constrained"] = final_constraints[key_mapping.get(area)]['max']
            allocation_details[area]['margin_per_unit'] = prices[
                allocation_to_margin_category.get(key_mapping.get(area))]

    current_recommendations = copy.deepcopy(allocation_details)
    st.session_state.optimizer_run = True
    st.session_state.duration = duration
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

        st.sidebar.write(f"Caustic Production: {round(dcs_constraints['caustic_production'], 2)} TPH")
        st.sidebar.write(f"H2 Generated: {round(dcs_constraints['caustic_production'], 2) * 280} NM3/hr")

        st.session_state.dashboard_data = new_recommendations

        # Save the initial optimizer state and recommendations to DB
        st.session_state.last_run_constraints = copy.deepcopy(initial_constraints_snapshot)
        save_optimizer_last_run_constraints(st.session_state.last_run_constraints)
        save_allocation_data(st.session_state.dashboard_data)  # Save initial recommendations to the allocations table

        st.success("Initial optimizer run completed and database seeded with default constraints!")
