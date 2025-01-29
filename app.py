import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values
import base64
import instructor

from models import PaintingInfo

st.set_page_config(page_title="Painting reader", layout="centered")

config = dotenv_values(".env")

def prepare_image_for_openai(image_file):

    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/png;base64,{image_data}"

def return_openai_instructor():
    openai_client = OpenAI(api_key=config["API_KEY"])
    instructor_openai_client = instructor.from_openai(openai_client)

    return instructor_openai_client



def generate_data_for_image(uploaded_files, response_model=PaintingInfo):
    responses = []
    for file in uploaded_files:
        
        res = return_openai_instructor().chat.completions.create(
            model="gpt-4o",
            response_model=response_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Pobierz szczegóły na temat obrazu.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": prepare_image_for_openai(file),
                                "detail": "high"
                            },
                        },
                    ],
                },
            ],
        )

        responses.append(res.model_dump())

    return responses



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
    st.success(f"Successfully loaded {len(uploaded_files)} image(s).")

if uploaded_files:

    tab_names = [file.name for file in uploaded_files]
    tabs = st.tabs(tab_names)
    
    with st.spinner("Generating painting details..."):
        responses = generate_data_for_image(uploaded_files=uploaded_files)

    for tab, file, response in zip(tabs, uploaded_files, responses):
        with tab:
            st.image(file, caption=file.name, use_container_width=True)
            st.write("### Opis obrazu:")
            st.write(response)
