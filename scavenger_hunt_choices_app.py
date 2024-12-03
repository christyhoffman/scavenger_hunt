import streamlit as st
import openai
from fpdf import FPDF
import os
import re
import textwrap

# Function to generate clues using OpenAI API
def generate_clues_for_locations(locations, theme, difficulty):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    clues = {}
    # Treat the last location differently
    last_location = locations[-1]
    for location in locations:
        if location == last_location:
            prompt = f"""
            Create three possible final clues for the following location that leads to a prize or gift:
            - Location: {location}
            Use the following theme:
            - Theme: {theme}
            Tailor the clue to this age group:
            - Age level: {age_level}
            Ensure the clue is rhyming, creative, and age-appropriate. 
            """
        else:
            prompt = f"""
            Create three unique scavenger hunt clues for the following location:
            - Location: {location}
            Use the following theme:
            - Theme: {theme}
            Tailor to this age group:
            - Age level: {age_level}
            Be mindful of the selected difficulty level:
            - Difficulty: {difficulty}
            The clue should be rhyming, creative, and age-appropriate.
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative scavenger hunt clue generator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            response_content = response.choices[0].message.content
            print(response_content)

            # Split and clean clues for regular locations
            if location != last_location:
                cleaned_clues = re.split(
                    r'(?:Clue\s*\w+[:.]?|(?:\d+[.:])|(?:Clue\s*[a-zA-Z]+[.:]?))\s*',
                    response_content
                )
                clues[location] = [
                    f'"{clue.strip()}"' if not clue.strip().startswith('"') and not clue.strip().endswith('"') else clue.strip()
                    for clue in cleaned_clues if clue.strip()
                ]
            else:
                # Keep the final location as a single, distinct clue
                cleaned_clues = re.split(
                    r'(?:Clue\s*\w+[:.]?|(?:\d+[.:])|(?:Clue\s*[a-zA-Z]+[.:]?))\s*',
                    response_content
                )
                clues[location] = [
                    f'"{clue.strip()}"' if not clue.strip().startswith('"') and not clue.strip().endswith('"') else clue.strip()
                    for clue in cleaned_clues if clue.strip()
                ]
                
        except Exception as e:
            st.error(f"Error generating clues for location '{location}': {e}")
            clues[location] = []
    return clues

# Function to save selected clues to a PDF
def save_clues_to_pdf(selected_clues, filename="scavenger_hunt.pdf"):
    pdf = FPDF()
    pdf.add_page()

    # Use a font with Unicode support
    pdf.set_font("helvetica", size=16)
    pdf.cell(0, 10, "Scavenger Hunt", ln=True, align='C')
    pdf.set_font("helvetica", size=12)

    for location, clue in selected_clues.items():
        # Add the location
        pdf.multi_cell(0, 10, f"Location: {location}")
        pdf.ln(2)  # Small spacing between location and clue

        # Replace non-ASCII characters and normalize spaces
        cleaned_clue = re.sub(r'[’‘]', "'", clue.strip())  # Replace curly quotes with straight quotes
        cleaned_clue = cleaned_clue.replace("“", '"').replace("”", '"')  # Replace curly double quotes
        cleaned_clue = re.sub(r'\s+', ' ', cleaned_clue)  # Normalize whitespace to a single space

        # Ensure only one set of quotes is used
        if cleaned_clue.startswith('"') and cleaned_clue.endswith('"'):
            cleaned_clue = cleaned_clue[1:-1]  # Remove surrounding quotes

        # Wrap text to create multiline output
        wrapped_clue = "\n".join(textwrap.wrap(cleaned_clue, width=80))  # Adjust width for line breaks
        
        # Add the wrapped clue to the PDF
        pdf.multi_cell(0, 10, f"\"{wrapped_clue}\"")
        pdf.ln(5)  # Add spacing between entries for readability

    pdf.output(filename)
    return filename
    

# Streamlit App
st.title("Scavenger Hunt Generator")
st.subheader("Create a customized scavenger hunt in minutes!")

# Input fields
theme = st.text_input("Enter the theme (e.g. Birthday Party, Buffalo Bills, Elf on the Shelf, Wild Animals):", "Harry Potter")

# Add a multiline description using markdown
st.markdown("""
Enter one specific location per line (e.g. on a shelf in the living room).  
Be sure to enter the location of the hidden gift or prize last.
""")

# Input field for locations
locations = st.text_area("Locations:").strip().split('\n')  # Trim and split input

difficulty = st.selectbox("Select difficulty level:", ["Easy", "Medium", "Hard"])

age_level = st.selectbox("Select an age level:", ["Preschool (3-4 years)", "Elementary (5-12 years)", "Teen (13-18 years)", "Adult"])

# Initialize or reset session state
if st.button("Generate Clues") or "clues" not in st.session_state:
    st.session_state.clues = {}  # Reset clues
    st.session_state.selected_clues = {}  # Reset selected clues

    # Process locations input
    locations = [loc.strip() for loc in locations if loc.strip()]
    if not locations:
        st.error("Please provide at least one location.")
    else:
        st.write("Generating your scavenger hunt clues...")
        st.session_state.clues = generate_clues_for_locations(locations, theme, difficulty)
        if st.session_state.clues:
            st.success("Clues generated successfully!")
        else:
            st.error("No clues were generated. Please try again.")

# Display clues and allow user selection
if st.session_state.clues:
    for location, clues in st.session_state.clues.items():
        st.subheader(f"Location: {location}")
        if location not in st.session_state.selected_clues:
            st.session_state.selected_clues[location] = ""

        # Display clues with radio buttons
        selected_clue = st.radio(
            f"Select one clue for {location}:",
            options=clues,
            key=f"radio_{location}"
        )
        st.session_state.selected_clues[location] = selected_clue

# Download PDF button
if any(st.session_state.selected_clues.values()):
    pdf_filename = "scavenger_hunt.pdf"
    save_clues_to_pdf(st.session_state.selected_clues, pdf_filename)
    with open(pdf_filename, "rb") as pdf_file:
        st.download_button(
            label="Download Selected Clues as PDF",
            data=pdf_file,
            file_name=pdf_filename,
            mime="application/pdf"
        )
