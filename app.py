import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values
import base64
import instructor
import os
from io import BytesIO
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
from models import PaintingInfo, New_paint

import tinify

# Constants
PRICE_FOR_IMAGE = 0.0000075
PRICE_FOR_TEXT = 0.00001
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 50  # Page margin in points
LINE_HEIGHT = 14  # Line height in points



# Initialize session state for token usage
if "total_tokens_used" not in st.session_state:
    st.session_state["total_tokens_used"] = 0

# Set up the page configuration
st.set_page_config(page_title="Painting Reader", layout="centered")

# Load environment variables
config = dotenv_values(".env")

#TINFY api key
# tinify.key = st.secrets["TINIFY"]
tinify.key = config["TINIFY"]



def setup_api_key():
    """Handles OpenAI API key setup using dotenv_values."""
    if not st.session_state.get("openai_key"):
        api_key = config.get("API_KEY")  # Fetch API key from .env file
        if api_key:
            st.session_state["openai_key"] = api_key
        else:
            st.info("Provide Your OpenAI API key to continue.")
            api_key_input = st.text_input("OpenAI API Key:", type="password")
            if api_key_input:
                st.session_state["openai_key"] = api_key_input
                st.rerun()  # Refresh the app to apply the key

    if not st.session_state.get("openai_key"):
        st.error("OpenAI API key is required to proceed.")
        st.stop()

# Handle API key setup
setup_api_key()

def create_pdf(uploaded_files: list, painting_responses: list, recommendations_dict: dict) -> str:
    """Generates a PDF report with images, descriptions, and recommendations."""

    pdf_path = "generated_painting_report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    y_position = add_title_to_pdf(c)
    
    for file_path, response in zip(uploaded_files, painting_responses):
        y_position = add_image_and_description(c, file_path, response, y_position)
        painting_title = response.get("title", os.path.basename(file_path))
        
        if painting_title in recommendations_dict:
            y_position = add_recommendations(c, y_position, recommendations_dict[painting_title])
        
        if y_position < MARGIN + 100:  # Add a new page if space is running out
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
    
    c.save()

    # Cleanup temporary files
    for file_path in uploaded_files:
        os.remove(file_path)

    return pdf_path

def add_title_to_pdf(c: canvas.Canvas) -> int:
    """Adds a title to the PDF and returns the updated Y position."""

    c.setFont("Courier-Bold", 28)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 50, "Painting Report - ArtExplorer")
    
    y_position = PAGE_HEIGHT - 80  # Adjust Y position after title
    
    # Add a separator line
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.line(MARGIN, y_position, PAGE_WIDTH - MARGIN, y_position)
    
    return y_position

def add_image_and_description(c: canvas.Canvas, file_path: str, response: dict, y_position: int) -> int:
    """Adds an image and its description to the PDF."""

    img_width, img_height = 400, 300  # Image dimensions

    if y_position - img_height < MARGIN:
        c.showPage()
        y_position = PAGE_HEIGHT - MARGIN

    y_position -= 50  # Adjust Y position for image
    c.drawImage(file_path, 100, y_position - img_height, width=img_width, height=img_height)
    y_position -= img_height + 45  # Adjust Y position after image

    # Add painting details
    title = response.get("title", "Unknown Title")
    author = response.get("author", "Unknown Author")
    year = response.get("year", "Unknown Year")
    description = response.get("description_of_historical_event_in_3_sentences", "No Description")

    c.setFont("Helvetica-Bold", 12)
    details = [f"Title: {title}", f"Author: {author}", f"Year: {year}", "Description:"]
    for line in details:
        if y_position - LINE_HEIGHT < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
        c.drawString(MARGIN, y_position, line)
        y_position -= LINE_HEIGHT

    y_position -= LINE_HEIGHT

    # Add description text
    c.setFont("Helvetica", 10)
    description_lines = simpleSplit(description, 'Helvetica', LINE_HEIGHT, PAGE_WIDTH - 2 * MARGIN)
    for line in description_lines:
        if y_position - LINE_HEIGHT < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
        c.drawString(MARGIN, y_position, line)
        y_position -= LINE_HEIGHT

    y_position -= LINE_HEIGHT

    return y_position

def add_recommendations(c: canvas.Canvas, y_position: int, recommendations: list) -> int:
    """Adds a section with recommended paintings to the PDF."""
    if not isinstance(recommendations, list):
        st.error(f"Expected recommendations to be a list, but got {type(recommendations)}")
        return y_position

    if not recommendations:
        return y_position  # Return y_position unchanged

    if y_position - 50 < MARGIN:
        c.showPage()
        y_position = PAGE_HEIGHT - MARGIN

    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN, y_position, "Recommended similar painting:")
    y_position -= 20

    c.setFont("Helvetica", 12)

    for rec in recommendations:
        text_lines = [
            f"Title: {rec.get('title', 'Unknown')}",
            f"Author: {rec.get('author', 'Unknown')}",
            f"Year: {rec.get('year', 'Unknown')}",
        ]
        for line in text_lines:
            c.drawString(MARGIN, y_position, line)
            y_position -= LINE_HEIGHT
        
        y_position -= 10  # Extra spacing between recommendations

    return y_position

def generate_pdf_button(uploaded_files: list):
    """Generates and provides a download button for the PDF."""
    if st.button("Generate PDF with Paintings and Recommendations"):
        if "painting_responses" not in st.session_state:
            st.error("Painting responses not available yet. Please generate painting details first.")
            return

        painting_responses = st.session_state["painting_responses"]

        if "recommendations" not in st.session_state:
            st.session_state["recommendations"] = {} 

        pdf_path = create_pdf(uploaded_files, painting_responses, st.session_state["recommendations"])

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            st.download_button(
                label="Download your PDF",
                data=pdf_data,
                file_name="Painting_Report.pdf",
                mime="application/pdf"
            )


#Functions for image_compression

def compress_image(uploaded_file):
    """ Compress an uploaded image using Tinify and return its temp file path"""
    file_bytes = BytesIO(uploaded_file.read())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_input:
        temp_input.write(file_bytes.getvalue())
        temp_input_path = temp_input.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_output:
        tinify.from_file(temp_input_path).to_file(temp_output.name)
        temp_output_path = temp_output.name

    return temp_output_path


def prepare_image_for_openai(image_file: BytesIO) -> str:
    """Prepares an image for OpenAI API by encoding it in base64."""
    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/png;base64,{image_data}"

def return_openai_instructor():
    """Returns an OpenAI client with instructor."""
    openai_client = OpenAI(api_key=st.session_state["openai_key"])
    instructor_openai_client = instructor.from_openai(openai_client)
    return instructor_openai_client

def calculate_token_cost(tokens_used: int, price_per_token: float) -> float:
    """Calculates the cost based on tokens used and price per token."""
    return tokens_used * price_per_token

def generate_data_for_text(painting_details: str, response_model=New_paint) -> list:
    """Generates data for text-based OpenAI requests."""
    try:
        res = return_openai_instructor().chat.completions.create(
            model="gpt-4o",
            response_model=response_model,
            temperature=1,
            messages=[
                {"role": "user", "content": f"Reccomend a new painting with similar style as: {painting_details} reply in english."}
            ],
        )
        response = res.model_dump()
        tokens_used = response['total_tokens_usage_cost_text_to_text']
        tokens_price = calculate_token_cost(tokens_used, PRICE_FOR_TEXT)
        st.session_state["total_tokens_used"] += tokens_price
        return [response]
    except Exception as e:
        st.error(f"Error generating data for text: {e}")
        return []

def generate_data_for_image(uploaded_files: list, response_model=PaintingInfo) -> list:
    """Generates data for image-based OpenAI requests."""
    responses = []
    for file in uploaded_files:
        try:
            res = return_openai_instructor().chat.completions.create(
                model="gpt-4o",
                response_model=response_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Collect details of the painting. Return information about used tokens. Reply in english and do not use polish letters",
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
            tokens_price = calculate_token_cost(tokens_used, PRICE_FOR_IMAGE)
            st.session_state["total_tokens_used"] += tokens_price
            responses.append(response)
        except Exception as e:
            st.error(f"Error generating data for image: {e}")
    return responses

def render_sidebar(uploaded_files: list):
    """Renders the sidebar with file uploader and cost display."""
    with st.sidebar:
        st.header("Upload Your Images :arrow_lower_left:")
        uploaded_files = st.file_uploader(
            label=" ",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg"]
        )

        if uploaded_files:

            #compress all uploaded images
            compressed_files = [compress_image(file) for file in uploaded_files]

            st.metric("Total Cost:", f"{round(st.session_state['total_tokens_used'], 4)}$")
            st.header("Download Your PDF")
            generate_pdf_button(compressed_files)

    return uploaded_files



def get_language_flags():
    return {
        "Polski 🇵🇱": "pl",
        "English 🇬🇧": "en",
        "Deutsch 🇩🇪": "de",
        "Français 🇫🇷": "fr",
        "Español 🇪🇸": "es"
    }

def render_main_ui():
    """Renders the main UI with title and description."""
    st.title("ArtExplorer :male-artist:")
    st.write(
        "Took a picture but forgot everything? Just upload your chosen paintings, "
        "and the AI will do the rest :handshake:"
    )

def handle_file_tabs(uploaded_files: list):
    """Handles the creation of tabs and file processing."""
    tab_names = [file.name for file in uploaded_files]
    tabs = st.tabs(tab_names)

    for tab, file in zip(tabs, uploaded_files):
        with tab:
            tab_key = f"tab_{file.name}"

            if tab_key not in st.session_state:
                st.session_state[tab_key] = None

            with st.form(key=f"form_{file.name}"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    submit_button = st.form_submit_button(
                        label=":arrow_right_hook: 1/2 Click Here to generate painting description",
                        type="tertiary"
                    )
                
                with col2:
                    language_flags = get_language_flags()
                    selected_language = st.selectbox(
                        "Select output language:", list(language_flags.keys()),
                        index=list(language_flags.keys()).index(st.session_state["selected_language"])
                    )
                    st.session_state["selected_language"] = selected_language  # Zapis do session_state
                    print(f'Wybrany jezyk to: {st.session_state["selected_language"]}')
                st.image(file, caption=file.name, use_container_width=True)


                if submit_button:
                    with st.spinner("Generating painting details..."):
                        try:
                            response = generate_data_for_image([file])[0]
                            st.session_state[tab_key] = response

                            if "painting_responses" not in st.session_state:
                                st.session_state["painting_responses"] = []

                            st.session_state["painting_responses"].append(response)
                        except Exception as e:
                            st.error(f"An error occurred: {e}")

                    st.rerun()

            if st.session_state[tab_key]:
                display_painting_details(st.session_state[tab_key], file)

def display_painting_details(response: dict, file: BytesIO):
    """Displays painting details and handles recommendations."""
    st.markdown(f"**Title:** {response['title']}")
    st.markdown(f"**Author:** {response['author']}")
    st.markdown(f"**Year:** {response['year']}")
    st.markdown(f"**Description:**")
    st.markdown(f"> {response['description_of_historical_event_in_3_sentences']}")

    rec_key = f"rec_{file.name}"
    if rec_key not in st.session_state:
        st.session_state[rec_key] = None

    with st.form(key=f"form_rec_{file.name}"):
        submit_recommendation = st.form_submit_button(
            label=":arrow_right_hook: 2/2 Looking for similar painting to see? Just click 🖍️",
            type="tertiary"
        )
        

        if submit_recommendation:
            with st.spinner("Generating recommendations..."):
                try:
                    recommendations = generate_data_for_text(response)
                    painting_title = response.get("title", file.name)

                    if isinstance(painting_title, str):
                        if "recommendations" not in st.session_state:
                            st.session_state["recommendations"] = {}
                        st.session_state["recommendations"][painting_title] = recommendations
                    else:
                        st.error("Painting title is not a string. Cannot store recommendations.")
                except Exception as e:
                    st.error(f"Error generating recommendations: {e}")

            st.rerun()

    if "recommendations" in st.session_state and st.session_state["recommendations"]:
        current_painting_title = response.get("title", file.name)
        if current_painting_title in st.session_state["recommendations"]:
            recommendations = st.session_state["recommendations"][current_painting_title]
            for idx, recommendation in enumerate(recommendations, start=1):
                st.markdown(f"**Title:** {recommendation.get('title', 'N/A')}")
                st.markdown(f"**Author:** {recommendation.get('author', 'N/A')}")
                st.markdown(f"**Year:** {recommendation.get('year', 'N/A')}")

# Render the UI
uploaded_files = render_sidebar(None)
render_main_ui()

# Render tabs and handle file processing
if uploaded_files:

    if "selected_language" not in st.session_state:
        st.session_state["selected_language"] = "Polski 🇵🇱"
    handle_file_tabs(uploaded_files)




