import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values
import base64
import instructor

PRICE_FOR_IMAGE = 0.0000075
PRICE_FOR_TEXT = 0.00001 

from models import PaintingInfo, New_paint

st.set_page_config(page_title="Painting reader", layout="centered")

config = dotenv_values(".env")

st.session_state["total_tokens_used"] = st.session_state.get("total_tokens_used", 0)


def prepare_image_for_openai(image_file):


    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/png;base64,{image_data}"

def return_openai_instructor():
    openai_client = OpenAI(api_key=config["API_KEY"])
    instructor_openai_client = instructor.from_openai(openai_client)

    return instructor_openai_client

def generate_data_for_text(painting_details, response_model=New_paint):

    print("WYKONUJE CALL OPENAI DLA TEXT")
    res = return_openai_instructor().chat.completions.create(
    model="gpt-4o",
    response_model=response_model,
    temperature=1,
    # n=2 #TODO bedzie to potrzebne do liczenia zuzycia
    messages=[
        {
            "role": "user",
            "content": f"""
            Zaproponuj sympatykowi sztuki 2 obrazy o podobnej tematyce co {painting_details}.
            Zwroc go w formacie Tytul, Autor oraz URL pod ktorym mozna ten obraz znalezc.
            Zwroc rowniez informacje o zuzytych tokenach do tego zapytania tak by mozna bylo to przeliczyc na koszt w dolarach.
            """,
        },
            ],
    
    )

    response = res.model_dump()
    tokens_used = response['total_tokens_usage_cost_text_to_text']
    tokens_price = float(tokens_used) * PRICE_FOR_TEXT
    print(f"{tokens_price} $")

    st.session_state["total_tokens_used"] += tokens_price
    


    return response
    
def generate_data_for_image(uploaded_files, response_model=PaintingInfo):

    print("WYKONUJE CALL OPENAI DLA OBRAZ")
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
                            "text": "Pobierz szczegóły na temat obrazu.Zwroc rowniez informacje o zuzytych tokenach do tego zapytania tak by mozna bylo to przeliczyc na koszt w dolarach.",
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

        response = res.model_dump()
        tokens_used = response['total_tokens_usage_cost_image_to_text'] 
        tokens_price = float(tokens_used) * PRICE_FOR_IMAGE
        print(f"{tokens_price} $")

        st.session_state["total_tokens_used"] += tokens_price



        responses.append(response)

    return responses

def update_token_usage_display():
    st.session_state["total_tokens_used_display"] = st.session_state["total_tokens_used"]



if not st.session_state.get("openai_key"):
    if "API_KEY" in config:
        st.session_state["openai_key"] = config["API_KEY"]

    
    else:
        st.info("Provide Your OPENAI API key to continue")
        st.session_state["openai_key"] = st.text_input("Klucz OPEN_AI: ")
        if st.session_state["openai_key"]:
            st.rerun()


if not st.session_state.get("openai_key"):
    st.stop()

st.title("ArtExplorer :male-artist:")

with st.sidebar:
    st.header("Upload Your images :arrow_lower_left:")
    uploaded_files = st.file_uploader(label=" ",
                                      accept_multiple_files=True,
                                      type=["png", "jpg", "jpeg", "gif", "bmp"])

    if uploaded_files:
        
        st.success(f"Successfully loaded {len(uploaded_files)} image(s).")
        st.write(f"Total cost: {st.session_state['total_tokens_used']}$")

        with st.form(key="refresh_tokens"):
            submit_button = st.form_submit_button(label="Refresh app cost")

        if submit_button:
            update_token_usage_display()
            



if uploaded_files:

    tab_names = [file.name for file in uploaded_files]
    tabs = st.tabs(tab_names)

    for tab, file in zip(tabs, uploaded_files):
        with tab:
            tab_key = f"tab_{file.name}"

            if tab_key not in st.session_state:
                st.session_state[tab_key] = None

            with st.form(key=f"form_{file.name}"):
                submit_button = st.form_submit_button(label="Generate Image Details & Recommendation", type="primary")
    
                if submit_button:
                    with st.spinner("Generating painting details..."):
                        try:
                            response = generate_data_for_image([file])[0]  # Pobieramy dane dla obrazu
                            st.session_state[tab_key] = response
                        except Exception as e:
                            st.error(f"An error occurred: {e}")

                    st.rerun()
    
            if st.session_state[tab_key]:
                response = st.session_state[tab_key]
                st.image(file, caption=file.name, use_container_width=True)
                st.markdown(f"**Title:** {response['title']}")
                st.markdown(f"**Author:** {response['author']}")
                st.markdown(f"**Year:** {response['year']}")
                st.markdown(f"**Description:**")
                st.markdown(f"> {response['description_of_historical_event_in_3_sentences']}")

                rec_key = f"rec_{file.name}"
                if rec_key not in st.session_state:
                    st.session_state[rec_key] = None

            # Formularz do generowania rekomendacji
                with st.form(key=f"form_rec_{file.name}"):
                    submit_recommendation = st.form_submit_button(label="Generate Recommendation", type="primary")

                    if submit_recommendation:
                        st.session_state[rec_key] = generate_data_for_text(response)
                        st.rerun()

            # Wyświetlenie rekomendacji, jeśli została wygenerowana
                if st.session_state[rec_key]:
                    with st.expander("Click here for new painting recommendation :arrow_double_down:"):
                        rec = st.session_state[rec_key]
                        st.markdown(f"**Title:** {rec['title']}")
                        st.markdown(f"**Author:** {rec['author']}")
                        st.markdown(f"**Year:** {rec['year']}")