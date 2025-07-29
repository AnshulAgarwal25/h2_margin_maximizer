from params import *
import numpy as np


def fix_bank_constraints(dcs_constraints, prices, constraints, final_constraints):
    # if dcs_constraints['header_pressure'] < constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max']:
    #     if dcs_constraints['number_of_banks'] < 1:
    #         prices['Bank'] = 0

    final_constraints['bank']['max'] = dcs_constraints['bank_available'] - (
            dcs_constraints['bank_available'] / dcs_constraints['number_of_banks'])
    if final_constraints['bank']['max'] < dcs_constraints['calculated_bank_flow']:
        final_constraints['bank']['max'] = dcs_constraints['calculated_bank_flow']

    if dcs_constraints['number_of_banks'] < 1:
        final_constraints['bank']['max'] = 0

    return prices, final_constraints


def fix_h2o2_constraints(dcs_constraints, constraints, final_constraints):
    # STEP 1: Getting consumption norm
    h2_consumption_norm = dcs_constraints['h2o2_h2_flow'] / dcs_constraints['h2o2_production']

    # STEP 2: Setting default values for stable conditions
    final_constraints['h2o2']['min'] = dcs_constraints['h2o2_h2_flow']
    final_constraints['h2o2']['max'] = dcs_constraints['h2o2_h2_flow']

    # STEP 3: Cases when header pressure breaches the max threshold
    if dcs_constraints['header_pressure'] >= constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max']:
        if dcs_constraints['pipeline_disruption_hrs'] < constraints['H2O2 Plant'][
            'Load increase/decrease time for H2O2 (hrs)']:
            final_constraints['h2o2']['min'] = dcs_constraints['h2o2_h2_flow']
            if dcs_constraints['h2o2_h2_flow'] <= 2400:
                final_constraints['h2o2']['max'] = min(2400,
                                                       (constraints['Marketing']['Demand - H2O2 (TPD)']['max'] / 24) *
                                                       h2_consumption_norm)
            elif dcs_constraints['h2o2_h2_flow'] < 3000:
                final_constraints['h2o2']['max'] = dcs_constraints['h2o2_h2_flow']
            else:
                final_constraints['h2o2']['max'] = min(
                    dcs_constraints['h2o2_h2_flow'] + (200 * dcs_constraints['pipeline_disruption_hrs']),
                    (constraints['H2O2 Plant']['H2O2 Production Capacity (TPD)']['max'] / 24) * h2_consumption_norm,
                    (constraints['Marketing']['Demand - H2O2 (TPD)']['max'] / 24) * h2_consumption_norm
                )

        else:
            final_constraints['h2o2']['min'] = dcs_constraints['h2o2_h2_flow']
            final_constraints['h2o2']['max'] = min(
                dcs_constraints['h2o2_h2_flow'] + (200 * dcs_constraints['pipeline_disruption_hrs']),
                (constraints['H2O2 Plant']['H2O2 Production Capacity (TPD)']['max'] / 24) * h2_consumption_norm,
                (constraints['Marketing']['Demand - H2O2 (TPD)']['max'] / 24) * h2_consumption_norm
            )

    # STEP 4: Handling edge cases when H2O2 is shutdown or ramping down
    if dcs_constraints['h2o2_h2_flow'] < 1900:
        final_constraints['h2o2']['min'] = dcs_constraints['h2o2_h2_flow']
        final_constraints['h2o2']['max'] = dcs_constraints['h2o2_h2_flow']

    return final_constraints


def fix_flaker_constraints(dcs_constraints, constraints, final_constraints):
    # Step 1: If Load is very less or trickle flow - match the min and max
    for i in range(3, 5):
        if dcs_constraints[f'flaker-{i}_h2_flow'] < 750:
            final_constraints[f'flaker-{i}']['min'] = dcs_constraints[f'flaker-{i}_h2_flow']
            final_constraints[f'flaker-{i}']['max'] = dcs_constraints[f'flaker-{i}_h2_flow']

    # Step 2: Under normal operating conditions - min and max are matched - current flow
    if dcs_constraints['header_pressure'] < constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max']:
        for i in range(3, 5):
            final_constraints[f'flaker-{i}']['min'] = dcs_constraints[f'flaker-{i}_h2_flow']
            final_constraints[f'flaker-{i}']['max'] = dcs_constraints[f'flaker-{i}_h2_flow']

    # Step 3: Under header pressure breach - but duration is less than changeover time
    if dcs_constraints['header_pressure'] >= constraints['H2 Plant']['Header Pressure Threshold (kgf/cm2)']['max']:
        if dcs_constraints['pipeline_disruption_hrs'] < constraints['Flaker Plant'][
            'Flaker - Changeover time (NG to mix) (hrs)']:
            for i in range(3, 5):
                final_constraints[f'flaker-{i}']['min'] = dcs_constraints[f'flaker-{i}_h2_flow']
                final_constraints[f'flaker-{i}']['max'] = dcs_constraints[f'flaker-{i}_h2_flow']
        else:
            if not np.isinf(dcs_constraints['flaker-3_consumption_norm']):
                if dcs_constraints['flaker-3_consumption_norm'] > 100:
                    final_constraints['flaker-3']['min'] = dcs_constraints['flaker-3_h2_flow']
                    final_constraints['flaker-3']['max'] = dcs_constraints['flaker-3_consumption_norm'] * \
                                                           dcs_constraints[
                                                               'flaker-3_load']
            if not np.isinf(dcs_constraints['flaker-4_consumption_norm']):
                if dcs_constraints['flaker-4_consumption_norm'] > 100:
                    final_constraints['flaker-4']['min'] = dcs_constraints['flaker-4_h2_flow']
                    final_constraints['flaker-4']['max'] = dcs_constraints['flaker-4_consumption_norm'] * \
                                                           dcs_constraints[
                                                               'flaker-4_load'] - (400 * (220 / 67))

    return final_constraints


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

        'bank': {'min': 0, 'max': min(dcs_constraints['bank_available'],
                                      constraints['H2 Plant']['Bank Compressor Capacity (NM3/hr)']['max'])},

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
                                constraints['Caustic Plant']['H2 generated (NM3) per ton of caustic'])},

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

    prices, final_constraints = fix_bank_constraints(dcs_constraints, prices, constraints, final_constraints)
    final_constraints = fix_h2o2_constraints(dcs_constraints, constraints, final_constraints)
    final_constraints = fix_flaker_constraints(dcs_constraints, constraints, final_constraints)

    return final_constraints, prices
