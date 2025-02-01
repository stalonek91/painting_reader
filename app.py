import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values
import base64
import instructor

from models import PaintingInfo, New_paint

st.set_page_config(page_title="Painting reader", layout="centered")

config = dotenv_values(".env")

def prepare_image_for_openai(image_file):

    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/png;base64,{image_data}"

def return_openai_instructor():
    openai_client = OpenAI(api_key=config["API_KEY"])
    instructor_openai_client = instructor.from_openai(openai_client)

    return instructor_openai_client

def generate_data_for_text(painting_details, response_model=New_paint):
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
    st.session_state["total_tokens_used"] += tokens_used
    print(f"PRINTUJE RESPONSE total usage: {tokens_used}")

    return response
    
    


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
        st.session_state["total_tokens_used"] += tokens_used
        
        print(f"PRINTUJE RESPONSE total usage for image {file.name}: {tokens_used}")

        responses.append(response)
        print(responses)
    return responses


st.session_state["total_tokens_used"] = st.session_state.get("total_tokens_used", 0)


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

st.title("ArtExplorer :male-artist:")

with st.sidebar:
    st.header("Upload Your images :arrow_lower_left:")
    uploaded_files = st.file_uploader(label=" ",
                                      accept_multiple_files=True,
                                      type=["png", "jpg", "jpeg", "gif", "bmp"])

    if uploaded_files:
        st.success(f"Successfully loaded {len(uploaded_files)} image(s).")

    st.write(st.session_state["total_tokens_used"])


if uploaded_files:

    tab_names = [file.name for file in uploaded_files]
    tabs = st.tabs(tab_names)
    
    with st.spinner("Generating painting details..."):
        try:
            responses = generate_data_for_image(uploaded_files=uploaded_files)

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

            st.markdown(f"**Tokens used for this image:** {response['total_tokens_usage_cost_image_to_text']}")

            if st.button("Generate Recommendation", key=f"btn_{file.name}"):
                reccomendation_response = generate_data_for_text(response)

                with st.expander("Click here for new painting recomendation :arrow_double_down:"):              
                    st.markdown(f"**Title:** {reccomendation_response['title']}")
                    st.markdown(f"**Author:** {reccomendation_response['author']}")
                    st.markdown(f"**Year:** {reccomendation_response['year']}")
                