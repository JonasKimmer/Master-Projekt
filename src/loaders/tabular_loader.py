import pandas as pd
import streamlit as st


@st.cache_data
def load_data(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    elif name.endswith(".xlsx"):
        return pd.read_excel(file)
    else:
        return pd.read_json(file)


def is_json_file(file) -> bool:
    return file.name.lower().endswith(".json")
