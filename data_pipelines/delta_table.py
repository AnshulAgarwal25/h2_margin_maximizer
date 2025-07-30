import decimal
import os
import streamlit as st
import numpy as np
import pyarrow.compute as pc
from deltalake import DeltaTable
from data_pipelines.bank_parameter_generation import get_bank_data, get_bank_compressors_data, vent_check
from database import save_norm_value, get_latest_norm_value

from parameters.constants import *
from parameters.credentials import *


def get_dcs_data_table(table_name):
    # Set credentials via environment variables for adlfs to work with DeltaTable
    print("Reading DCS Data...")
    os.environ["AZURE_STORAGE_ACCOUNT_NAME"] = storage_account_name
    os.environ["AZURE_STORAGE_ACCOUNT_KEY"] = storage_account_key

    storage_options = {"account_name": storage_account_name,
                       "account_key": storage_account_key,
                       }
    delta_table_path = f"abfss://{container_name}@{storage_account_name}.dfs.core.windows.net/Margin_Maximizer_db/external/{table_name}"
    dt = DeltaTable(delta_table_path, storage_options=storage_options)
    table = dt.to_pyarrow_table()
    sorted_indices = pc.sort_indices(table, sort_keys=[("TimeStamp", "descending")])
    sorted_table = pc.take(table, sorted_indices[:10])

    pdf = sorted_table.to_pandas()
    pdf.rename(columns=column_name_mapping, inplace=True)
    return pdf


def populate_latest_dcs_constraints():
    data = get_dcs_data_table(table_name='DCS_Tag1_st')
    data = data.apply(np.vectorize(lambda x: float(x) if isinstance(x, decimal.Decimal) else x))
    data = data.fillna(0)
    print("DCS Data Fetched")
    st.session_state.dcs_raw_data = data

    data = data.iloc[:1]

    caustic_production = (data['Caustic_Caustic Production_332tpd_TPH'].values[0] +
                          data['Caustic_Caustic Production_450tpd_TPH'].values[0] +
                          data['Caustic_Caustic Production_600tpd_TPH'].values[0] +
                          data['Caustic_Caustic Production_850tpd_TPH'].values[0]) / 24  # original data in TPD

    # pipeline_flow = data['Hydrogen_Pipeline_current_NM3_per_hr'].values[0]
    pipeline_flow = (data['AARTI_H2_PIPELINE_SUPPLY'].values[0] + data['FARMSON_H2_PIPELINE_SUPPLY'].values[0] +
                     data['VALIANT_1_H2_PIPELINE_SUPPLY'].values[0] + data['GULSHANH2_PIPELINE_SUPPLY'].values[0] +
                     data['PANOLIH2_PIPELINE_SUPPLY'].values[0] + data['VALIANT_2_H2_PIPELINE_SUPPLY'].values[0] +
                     data['CHEMIE_H2_PIPELINE_SUPPLY'].values[0] + data['LANXESS_H2_PIPELINE_SUPPLY'].values[0] +
                     data['ANUPAM_RASAYAN_H2_PIPELINE_SUPPLY'].values[0] + data['UPL_5_H2_PIPELINE_SUPPLY'].values[0])

    header_pressure = data['Hydrogen_Header_pressure_current_kgf_per_cm2'].values[0]

    bank_available_quantity, number_of_banks_available = get_bank_data(data)

    # original data in TPD
    hcl_production = (data['1350TPD_HCL_FURNACE_1'].values[0] + data['1350TPD_HCL_FURNACE_2'].values[0] +
                      data['1350TPD_HCL_FURNACE_3'].values[0] + data['1350TPD_HCL_FURNACE_4'].values[0] +
                      data['850TPD_HCL_FURNACE_A'].values[0] + data['850TPD_HCL_FURNACE_B'].values[0]) / 24

    h2o2_production = data['H2O2_H2O2_current_TPH'].values[0] / 1000  # original data in KG/H
    flaker1_load = data['Flaker_450tpd_current_load_TPH'].values[0] / 24  # original data in TPD
    flaker2_load = data['Flaker_600tpd_current_load_TPH'].values[0] / 24  # original data in TPD
    flaker3_load = data['Flaker_850tpd_current_load_TPH_1'].values[0] / 24  # original data in TPD
    flaker4_load = data['Flaker_850tpd_current_load_TPH_2'].values[0] / 24  # original data in TPD

    flaker3_consumption_norm = (data['Flaker_850tpd_running_or_not_binary_1'].values[0] + (
            data['NG_flow_in_Flaker3'].values[0] * (220 / 67))) / (
                                       data['Flaker_850tpd_current_load_TPH_1'].values[0] / 24)

    flaker4_consumption_norm = (data['Flaker_850tpd_running_or_not_binary_2'].values[0] + (
            data['NG_flow_in_Flaker4'].values[0] * (220 / 67))) / (
                                       data['Flaker_850tpd_current_load_TPH_2'].values[0] / 24)

    boiler_p60_run = 1 if data['Boiler_P60_running_or_not_binary'].values[0] > 0 else 0
    boiler_p120_run = 1 if data['Boiler_P120_running_or_not_binary'].values[0] > 0 else 0

    ech_flow = data['ECH_H2_PIPELINE_SUPPLY'].values[0]

    h2_in_hcl = (data['H2_FLOW_TO_HCL_FURNACE_1'].values[0] + data['H2_FLOW_TO_HCL_FURNACE_2'].values[0] +
                 data['H2_FLOW_TO_HCL_FURNACE_3'].values[0] + data['H2_FLOW_TO_HCL_FURNACE_4'].values[0] +
                 data['H2_FLOW_TO_HCL_FURNACE_5'].values[0] + data['H2_FLOW_TO_HCL_FURNACE_6'].values[0])

    flaker1_flow = data['Flaker_450tpd_running_or_not_binary'].values[0]
    flaker2_flow = data['Flaker_600tpd_running_or_not_binary'].values[0]

    venting_check = vent_check(data)

    total_bank_flow = get_bank_compressors_data(data)
    bank_in_filling = 1 if total_bank_flow > 0 else 0

    dcs_constraints = {
        "332tpd_caustic": data['Caustic_Caustic Production_332tpd_TPH'].values[0],
        "450tpd_caustic": data['Caustic_Caustic Production_450tpd_TPH'].values[0],
        "600tpd_caustic": data['Caustic_Caustic Production_600tpd_TPH'].values[0],
        "850tpd_caustic": data['Caustic_Caustic Production_850tpd_TPH'].values[0],

        "caustic_production": caustic_production,
        "pipeline_flow": pipeline_flow,
        "header_pressure": header_pressure,
        "bank_available": bank_available_quantity,
        'hcl_production': hcl_production,
        "h2o2_production": h2o2_production,
        "flaker-1_load": flaker1_load,
        "flaker-2_load": flaker2_load,
        "flaker-3_load": flaker3_load,
        "flaker-4_load": flaker4_load,
        "flaker-3_consumption_norm": flaker3_consumption_norm,
        "flaker-4_consumption_norm": flaker4_consumption_norm,
        "boiler_p60_run": boiler_p60_run,
        "boiler_p120_run": boiler_p120_run,
        "hcl_h2_flow": h2_in_hcl + ech_flow,
        "h2o2_h2_flow": data['H2O2_H2_current_NM3_per_hr'].values[0],
        "flaker-1_h2_flow": flaker1_flow,
        "flaker-2_h2_flow": flaker2_flow,
        "flaker-3_h2_flow": data['Flaker_850tpd_running_or_not_binary_1'].values[0],
        "flaker-4_h2_flow": data['Flaker_850tpd_running_or_not_binary_2'].values[0],
        "pipeline_disruption_hrs": data['pipeline_disruption_hrs'].values[0],
        "is_bank_on": bank_in_filling,
        "is_vent_on": venting_check,
        "number_of_banks": number_of_banks_available,
        "calculated_bank_flow": total_bank_flow,
        "total_h2_flow": (pipeline_flow + h2_in_hcl + ech_flow + total_bank_flow +
                          data['Flaker_450tpd_running_or_not_binary'].values[0] +
                          data['Flaker_600tpd_running_or_not_binary'].values[0] +
                          data['Flaker_850tpd_running_or_not_binary_1'].values[0] +
                          data['Flaker_850tpd_running_or_not_binary_2'].values[0] +
                          data['H2O2_H2_current_NM3_per_hr'].values[0] +
                          data['Boiler_P60_current_H2_NM3_per_hr'].values[0] +
                          data['Boiler_P120_current_H2_NM3_per_hr'].values[0])
    }

    balance = (caustic_production * 280) - (pipeline_flow + total_bank_flow +
                                            h2_in_hcl + ech_flow +
                                            data['Flaker_450tpd_running_or_not_binary'].values[0] +
                                            data['Flaker_600tpd_running_or_not_binary'].values[0] +
                                            data['Flaker_850tpd_running_or_not_binary_1'].values[0] +
                                            data['Flaker_850tpd_running_or_not_binary_2'].values[0] +
                                            data['H2O2_H2_current_NM3_per_hr'].values[0] +
                                            data['Boiler_P60_current_H2_NM3_per_hr'].values[0] +
                                            data['Boiler_P120_current_H2_NM3_per_hr'].values[0])

    current_flow = {
        "pipeline": pipeline_flow,
        "bank": total_bank_flow if bank_in_filling == 1 else 0,
        "ech_flow": ech_flow,
        "hcl": h2_in_hcl + ech_flow,
        "flaker-1": 0 if flaker1_flow < 10 else flaker1_flow,
        "flaker-2": 0 if flaker2_flow < 10 else flaker2_flow,
        "flaker-3": data['Flaker_850tpd_running_or_not_binary_1'].values[0],
        "flaker-4": data['Flaker_850tpd_running_or_not_binary_2'].values[0],
        "h2o2": data['H2O2_H2_current_NM3_per_hr'].values[0],
        "boiler_p60": data['Boiler_P60_current_H2_NM3_per_hr'].values[0],
        "boiler_p120": data['Boiler_P120_current_H2_NM3_per_hr'].values[0],
        "vent": balance if venting_check == 1 else 0
    }
    dcs_constraints = {k: round(v if v >= 0 else 0, 2) for k, v in dcs_constraints.items()}
    current_flow = {k: round(v if v >= 0 else 0, 2) for k, v in current_flow.items()}

    caustic_production_norm = process_norm(dcs_constraints)
    dcs_constraints["caustic_production_norm"] = round(caustic_production_norm, 2)

    return dcs_constraints, current_flow


def process_norm(dcs_constraints):
    if dcs_constraints["is_vent_on"] == 0:
        caustic_production_norm = dcs_constraints['total_h2_flow'] / dcs_constraints['caustic_production']
        save_norm_value(caustic_production_norm)
    else:
        caustic_production_norm = get_latest_norm_value()

    return caustic_production_norm
