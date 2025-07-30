from io import BytesIO
import io
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


def load_data_for_report(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.floor("h")

    alloc_cols = [col for col in df.columns if col.endswith("_allocated")]
    reco_cols = [col.replace("_allocated", "_recommended") for col in alloc_cols]
    areas = [col.replace("_allocated", "") for col in alloc_cols]

    return df, alloc_cols, reco_cols, areas


def get_daily_report():
    if st.sidebar.button("📥 Download Daily Report"):
        df = fetch_data()
        df, alloc_cols, reco_cols, areas = load_data_for_report(df)
        # Step 1: Aggregate to hourly level first (if needed)
        hourly_df = df.groupby(["date", "hour"]).sum(numeric_only=True).reset_index()

        # Step 2: Aggregate hourly to daily
        daily_df = hourly_df.groupby("date").sum(numeric_only=True).reset_index()

        # Step 3: Create a report for each date
        records = []

        for _, row in daily_df.iterrows():
            date = row["date"]
            record = {"Date": date}
            for area, alloc_col, reco_col in zip(areas, alloc_cols, reco_cols):
                allocated = row.get(alloc_col, 0)
                recommended = row.get(reco_col, 0)
                margin_col = f"{area}_margin_per_unit"
                margin = df[margin_col].mean() if margin_col in df.columns else 0
                difference = allocated - recommended
                difference = 0 if abs(difference) < 5 else difference
                value_diff = difference * margin
                record.update({
                    f"{area} Allocated": allocated,
                    f"{area} Recommended": recommended,
                    f"{area} Diff": difference,
                    f"{area} Value Diff (₹)": value_diff
                })
            records.append(record)

        final_df = pd.DataFrame(records)

        # Export to Excel in memory
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False, sheet_name="Daily_Report")

        buffer.seek(0)
        st.sidebar.download_button(
            label="📄 Click to Download Daily Report Excel",
            data=buffer.getvalue(),
            file_name="daily_allocation_report_by_date.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


def get_adherence_report():
    if st.sidebar.button("📥 Download Adherence Report"):
        df = fetch_data()
        df, alloc_cols, reco_cols, areas = load_data_for_report(df)
        # --- Compute Adherence % ---
        adherence = {}
        for alloc, reco in zip(alloc_cols, reco_cols):
            area = alloc.replace("_allocated", "")
            adherence[area] = (df[alloc] == df[reco]).sum() / len(df)

        adherence_df = pd.DataFrame.from_dict(adherence, orient="index", columns=["Adherence %"])
        adherence_df["Adherence %"] = (adherence_df["Adherence %"] * 100).round(2)

        # --- Count Rejected Status and Comments ---
        status_cols = [col for col in df.columns if col.endswith("_status")]
        comment_cols = [col for col in df.columns if col.endswith("_comment")]

        total_rejected = sum((df[col] == "rejected").sum() for col in status_cols)
        total_comments = sum(df[col].astype(str).str.strip().ne("").sum() for col in comment_cols)

        # --- Prepare summary as an extra sheet ---
        summary = pd.DataFrame({
            "Metric": ["Total Records", "Total 'rejected' statuses", "Total non-empty comments"],
            "Value": [len(df), total_rejected, total_comments]
        })

        # --- Save to Excel in memory ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            adherence_df.reset_index().rename(columns={"index": "Allocation Point"}).to_excel(
                writer, index=False, sheet_name="Adherence %")
            summary.to_excel(writer, index=False, sheet_name="Summary")

        # --- Download Button ---
        buffer.seek(0)
        st.sidebar.download_button(
            label="📄 Click to Download Adherence Report Excel",
            data=buffer.getvalue(),
            file_name="adherence_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
