import streamlit as st
import pandas as pd
import os
from datetime import datetime

HISTORY_FILE = "data/history.csv"
COLUMNS = ["Timestamp", "User", "Mode", "Source_Lang", "Target_Lang", "Input_Text", "Translated_Text"]

def _ensure_file_exists():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(HISTORY_FILE, index=False)
    else:
        # Auto-migrate old CSV format if it doesn't have the 'User' column
        try:
            df = pd.read_csv(HISTORY_FILE)
            if "User" not in df.columns:
                pd.DataFrame(columns=COLUMNS).to_csv(HISTORY_FILE, index=False)
        except Exception:
            pass

@st.cache_data(ttl=60, show_spinner=False)
def get_history(username):
    _ensure_file_exists()
    try:
        df = pd.read_csv(HISTORY_FILE)
        if df.empty or "User" not in df.columns:
            return pd.DataFrame(columns=COLUMNS)
        # Filter to only show this user's translations
        user_df = df[df["User"] == username]
        return user_df
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return pd.DataFrame(columns=COLUMNS)

def save_translation(username, mode, src_lang, tgt_lang, input_text, translated_text):
    _ensure_file_exists()
    new_row = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User": username,
        "Mode": mode,
        "Source_Lang": src_lang.capitalize(),
        "Target_Lang": tgt_lang.capitalize(),
        "Input_Text": input_text,
        "Translated_Text": translated_text,
    }])
    new_row.to_csv(HISTORY_FILE, mode="a", header=False, index=False)
    get_history.clear()

def clear_history(username):
    _ensure_file_exists()
    try:
        df = pd.read_csv(HISTORY_FILE)
        if "User" in df.columns:
            # Keep rows that do NOT belong to the current user
            df = df[df["User"] != username]
            df.to_csv(HISTORY_FILE, index=False)
        else:
            pd.DataFrame(columns=COLUMNS).to_csv(HISTORY_FILE, index=False)
    except Exception:
        pd.DataFrame(columns=COLUMNS).to_csv(HISTORY_FILE, index=False)
    get_history.clear()