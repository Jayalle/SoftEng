import en_core_web_sm
import streamlit as st
import pandas as pd
import base64
import datetime
import random
import io
import nltk

# Ensure NLTK data path includes the correct directory
nltk.data.path.append("../Uploaded_Resumes")

# Download NLTK resources if not already downloaded
nltk.download("stopwords")
nltk.download("punkt")

from pydparser import ResumeParser
from pdfminer.high_level import extract_text
from PIL import Image
import sqlite3
import spacy

nltk.download("stopwords")
nltk.download("punkt")


# Function to read PDF and return text
def pdf_reader(file):
    text = extract_text(file)
    return text

# Function to display PDF
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Function to insert data into MySQL database
def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):

    connection = sqlite3.connect("se2project.db")
    cursor = connection.cursor()
    DB_table_name = 'user_data'
    insert_sql = f"INSERT INTO {DB_table_name} VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    rec_values = (None,name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills,
                  recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()
    connection.close()

# Main function to run the application
def run():
    st.title("SkillSync: Job Recommendation")
    choice = "Normal User"

    # Handling database and tables
    connection = sqlite3.connect("se2project.db")

    cursor = connection.cursor()
    table_sql = """
                CREATE TABLE IF NOT EXISTS user_data (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Name VARCHAR(100) NOT NULL,
                    Email_ID VARCHAR(50) NOT NULL,
                    Resume_Score VARCHAR(8) NOT NULL,
                    Timestamp VARCHAR(50) NOT NULL,
                    Page_no VARCHAR(5) NOT NULL,
                    Predicted_Field VARCHAR(25) NOT NULL,
                    User_level VARCHAR(30) NOT NULL,
                    Actual_skills VARCHAR(300) NOT NULL,
                    Recommended_skills VARCHAR(300) NOT NULL,
                    Recommended_courses VARCHAR(600) NOT NULL
                );
                """
    cursor.execute(table_sql)

    # Normal User functionality
    if choice == 'Normal User':
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()

            if resume_data:
                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))

                    skills_df = pd.DataFrame(resume_data["skills"], columns=["SKILLS"])
                    st.table(skills_df)

                    experience_df = pd.DataFrame(resume_data["experience"], columns=["EXPERIENCES"])
                    st.table(experience_df)
                except KeyError:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)

                # Insert data into database
                insert_data(resume_data['name'], resume_data['email'], 'NA', str(datetime.datetime.now()),
                            resume_data['no_of_pages'], 'NA', cand_level, str(resume_data['skills']),
                            'NA', 'NA')


# Run the application pip install -U spacy
if __name__ == '__main__':
    run()
