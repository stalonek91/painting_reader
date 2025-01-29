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

    return res.model_dump()



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
    st.image(uploaded_files, width=400)

    st.write("Opis obrazka: ")

    st.write(generate_data_for_image(uploaded_files=uploaded_files))


