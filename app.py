import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values
import base64
import instructor

from models import PaintingInfo

st.set_page_config(page_title="Painting reader", layout="centered")

config = dotenv_values(".env")


st.title("Painting reader")
uploaded_files = st.file_uploader(label="Zalacz pliki z Twoimi obrazami", accept_multiple_files=True)

if uploaded_files:
    st.success(f"Successfully loaded {len(uploaded_files)} image(s).")

    for image in uploaded_files:
        st.image(image)

        print(f"Preparing openai")
        image_description = send_openai_query(image)
        st.write(image_description)


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
    st.success(f"Successfully loaded {len(uploaded_files)} image(s).")

    for image in uploaded_files:
        st.image(image)

        print(f"Preparing openai")
        image_description = send_openai_query(image)
        st.write(image_description)




