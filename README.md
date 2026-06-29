# DPI v1.0

Clean Streamlit Cloud-safe version.

## Files

- app.py
- requirements.txt
- README.md
- .streamlit/config.toml

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Main file path:

```text
app.py
```

## Notes

This version deliberately uses a single `app.py` and avoids `st.slider` because earlier deployments failed due to module imports and Streamlit frontend slider loading issues.
