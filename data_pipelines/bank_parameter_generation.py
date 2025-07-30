# def check_bank_filling_status(data):
#     bank_filling_status = False
#
#     for i in range(1, 4):
#         tag = f'H2_Bank_Pressure_Tag_{i}'
#         # checking if current bank pressure is the same as the value 3 mins before
#         if data[tag].iloc[3] != data[tag].iloc[0]:
#             bank_filling_status = True
#
#     return bank_filling_status


def get_bank_data(data):
    bank_available = 0
    number_of_banks_available = 0
    for i in range(1, 8):  # 1 to 7 inclusive
        post_prefix = f'H2_POST_{i}_BANK'
        number_of_banks = (
                data[f'{post_prefix}_IN_FILLING'].values[0] +
                data[f'{post_prefix}_AVAILABLE'].values[0] +
                data[f'{post_prefix}_FILLING__HOLD'].values[0]
        )

        available = number_of_banks * data[f'{post_prefix}_CAPACITY'].values[0]

        bank_available += available
        number_of_banks_available += number_of_banks

    return bank_available, number_of_banks_available


def get_bank_compressors_data(data):
    number_of_compressors_on = (
            data['Bank_compressor_status_ZH'].values[0] + data['Bank_compressor_status_ZI'].values[0] +
            data['Bank_compressor_status_ZJ'].values[0] + data['Bank_compressor_status_G'].values[0] +
            data['Bank_compressor_status_K'].values[0] + data['Bank_compressor_status_L'].values[0] +
            data['Bank_compressor_status_M'].values[0] + data['Bank_compressor_status_N'].values[0] +
            data['Bank_compressor_status_O'].values[0] + data['Bank_compressor_status_P'].values[0])

    total_bank_flow = number_of_compressors_on * 440
    return total_bank_flow


def vent_check(data):
    venting = 1 if (data['H2_vent_valve_CMD_332'].values[0] +
                    data['H2_vent_valve_CMD_450'].values[0] +
                    data['H2_vent_valve_CMD_600'].values[0] +
                    data['H2_vent_valve_CMD_850'].values[0]) > 3 else 0

    if (data['Hydrogen_Holder_level_current_per_1'].values[0] > 90 or
            data['Hydrogen_Holder_level_current_per_2'].values[0] > 90):
        venting = 1
    return venting
