from io import BytesIO

import pandas as pd
import streamlit as st

from database import load_all_allocations


def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


def fetch_data():
    all_allocations_df = load_all_allocations()
    print("\nSuccessfully loaded allocations data:")
    print(f"\nTotal rows: {len(all_allocations_df)}")
    return all_allocations_df


def fetch_audit_data():
    audit_df = pd.read_csv("data/audit_log.csv")
    print("\nSuccessfully loaded audit data:")
    print(f"\nTotal rows: {len(audit_df)}")
    return audit_df


def downloader_allocation():
    if st.sidebar.button("Prepare Allocation History File"):
        df = fetch_data()
        excel_data = to_excel(df)

        st.sidebar.download_button(
            label="Download",
            data=excel_data,
            file_name='allocation_history.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


def downloader_audit():
    if st.sidebar.button("Prepare Audit History File"):
        df = fetch_audit_data()
        excel_data = to_excel(df)

        st.sidebar.download_button(
            label="Download",
            data=excel_data,
            file_name='audit_log.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
