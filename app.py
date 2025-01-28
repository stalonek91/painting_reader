import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values

st.set_page_config(page_title="Painting reader", layout="centered")

config = dotenv_values(".env")

def get_openai_key():
    return OpenAI(api_key=st.session_state["openai_key"])

if not st.session_state.get("openai_key"):
    if "API_KEY" in config:
        st.session_state["openai_key"] = config["API_KEY"]
        # st.write(st.session_state["openai_key"])
    
    else:
        st.info("Provide Your OPENAI API key to continue")

