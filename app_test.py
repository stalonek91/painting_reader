import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values
import base64
import instructor
import json
import os

from models import PaintingInfo


st.set_page_config(page_title="Painting reader", layout="centered")

config = dotenv_values(".env")

def prepare_image_for_openai(image_file):

    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/png;base64,{image_data}"

def return_json_output():
    with open('json_test.json', "r", encoding="utf-8") as file:
        test_data = json.load(file)

    return test_data

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

with st.sidebar:
    uploaded_files = st.file_uploader(label="Zalacz pliki z Twoimi obrazami", accept_multiple_files=True)

    if uploaded_files:
        st.success(f"Successfully loaded {len(uploaded_files)} image(s).")



if uploaded_files:

    tab_names = [file.name for file in uploaded_files]
    tabs = st.tabs(tab_names)
    
    with st.spinner("Generating painting details..."):
        try:
            responses = return_json_output()

        except Exception as e:
            st.error(f"An error occurred: {e}")

            

    for tab, file, response in zip(tabs, uploaded_files, responses):
        with tab:
            st.image(file, caption=file.name, use_container_width=True)
            st.markdown(f"**Title:** {response['title']}")
            st.markdown(f"**Author:** {response['author']}")
            st.markdown(f"**Year:** {response['year']}")
            
            # Możemy dodać opis jako tekst w 3 zdaniach
            st.markdown(f"**Description:**")
            st.markdown(f"> {response['description_of_historical_event_in_3_sentences']}")
            print(type(response))

