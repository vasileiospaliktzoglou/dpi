# EXECUTE v6.10.3 Internal Excel Memory

This version keeps the workbook as the application's private data memory rather than a download button.

## Changes
- Removed XEON and U03A from the Daily Intelligence ETF universe.
- Removed the user name from report/email text.
- Removed the Excel download button.
- Excel is now internal app storage at `data/PALI_EXECUTE_DATA.xlsx`.
- The workbook is automatically updated when Daily Intelligence runs.
- Duplicate Streamlit reruns are handled with same-day upsert logic instead of endless duplicate rows.
- Added internal sheets for future learning:
  - Dashboard
  - Daily_Intelligence
  - Recommendations
  - ETF_Prices
  - Feature_Store
  - Learning
  - Reports
  - Settings
- Daily backups are created in `data/backups/`.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important
The Excel workbook is the application's local knowledge base. It is designed to be used by future versions of the prediction/deployment engine, not as a manual report download.
