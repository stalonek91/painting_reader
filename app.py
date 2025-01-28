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
        st.session_state["openai_key"] = st.text_input("Klucz OPEN_AI: ")
        if st.session_state["openai_key"]:
            st.rerun()


if not st.session_state.get("openai_key"):
    st.stop()

st.title("Painting reader")
uploaded_files = st.file_uploader(label="Zalacz pliki z Twoimi obrazami", accept_multiple_files=True)

if uploaded_files:
    for image in uploaded_files:
        st.image(image)