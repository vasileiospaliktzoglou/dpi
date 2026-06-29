# PALI Execute v6.10 - Daily Intelligence Edition

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## New in v6.10

Added a **Daily Intelligence** page that provides:

- Plain-English market explanation
- Current regime classification
- ETF-specific deployment window estimates
- Best estimated time window for V60A, VNGA80, VWCE, XEON and U03A
- Guardrails for each ETF
- Downloadable daily email draft in TXT and HTML

## Important

This version does **not** execute orders and does **not** send email automatically yet. It generates the intelligence report and email draft safely. The next step is to connect SMTP/Gmail and schedule it after Xetra close.
