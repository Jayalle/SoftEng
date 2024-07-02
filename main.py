import streamlit as st
import pandas as pd
import base64
import datetime
import nltk
import sqlite3
from pydparser import ResumeParser
from pdfminer.high_level import extract_text
from PIL import Image

##TODO: pip install openpyxl if error


# Ensure NLTK data path includes the correct directory
nltk.data.path.append("../Uploaded_Resumes")

# Download NLTK resources if not already downloaded
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
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Function to insert data into SQLite database
def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    connection = sqlite3.connect("se2project.db")
    cursor = connection.cursor()
    DB_table_name = 'user_data'
    insert_sql = f"INSERT INTO {DB_table_name} VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    rec_values = (None, name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()
    connection.close()

# Function to recommend jobs based on the resume
def recommend_jobs(field, skills):
    csv_files = {
        'Data Science': './CSV_files/data_scientist.xlsx',
        'Web Development': './CSV_files/web_developer.xlsx',
        'Android Development': './CSV_files/android_dev.xlsx',
        'IOS Development': './CSV_files/ios_dev.xlsx',
        'UI-UX Development': './CSV_files/ui_ux.xlsx',
        'Java Development': './CSV_files/java_dev.xlsx',
        'Development Operations Manager': './CSV_files/dev_ops.xlsx',
        'IT Security Specialist': './CSV_files/it_sec.xlsx',
        'Application Analyst': './CSV_files/app_analyst.xlsx',
        'Business Intelligence Analyst': './CSV_files/bi_analyst.xlsx',
        'Software Test Engineer': './CSV_files/test_eng.xlsx',
        'Database Administrator':'./CSV_files/db_admin.xlsx',
        'Information Technology Manager': './CSV_files/it_man.xlsx'
    }

    if field not in csv_files:
        return []

    try:
        df = pd.read_excel(csv_files[field])
    except UnicodeDecodeError:
        df = pd.read_excel(csv_files[field], encoding='latin1')

    recommended_jobs = []
    for index, row in df.iterrows():
        # Convert description to string and handle NaN values
        job_description = str(row['description']).lower() if pd.notna(row['description']) else ''
        job_keywords = job_description.split()
        matched_skills = [skill for skill in skills if skill.lower() in job_keywords]
        similarity_score = len(matched_skills)  # Simple count of matched skills as similarity score

        if matched_skills:
            recommended_jobs.append({
                'Title': row['title'],
                'Company': row['company'],
                'Location': row['location'],
                'Job URL': row['job_url'],
                'Matched Skills': matched_skills,
                'Similarity Score': similarity_score
            })

    # Sort recommended jobs by similarity score (descending)
    recommended_jobs.sort(key=lambda x: x['Similarity Score'], reverse=True)

    return recommended_jobs[:10]  # Return top 10 jobs based on similarity score

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
    connection.close()

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
                    st.markdown('<h4 style="text-align: left; color: #d73b5c;">You are looking Fresher.</h4>', unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('<h4 style="text-align: left; color: #1ed760;">You are at intermediate level!</h4>', unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('<h4 style="text-align: left; color: #fba171;">You are at experience level!</h4>', unsafe_allow_html=True)

                # Insert data into database
                insert_data(resume_data['name'], resume_data['email'], 'NA', str(datetime.datetime.now()), resume_data['no_of_pages'], 'NA', cand_level, str(resume_data['skills']), 'NA', 'NA')

                # Job recommendation logic
                recommended_skills = []
                reco_field = ''
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node js', 'react js', 'php', 'laravel', 'magento', 'wordpress', 'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes', 'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator', 'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro', 'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp', 'user research', 'user experience']
                java_dev_keywords = ['java developer', 'java', 'jdk', 'spring', 'hibernate', 'maven', 'gradle']
                dev_ops_manager_keywords = ['development operations manager', 'devops', 'continuous integration', 'continuous deployment', 'docker', 'kubernetes', 'jenkins']
                it_security_keywords = ['it security specialist', 'cybersecurity', 'network security', 'information security', 'firewall', 'penetration testing']
                application_analyst_keywords = ['application analyst', 'application support', 'business analyst', 'software analyst']
                bi_analyst_keywords = ['business intelligence analyst', 'bi analyst', 'data analyst', 'data visualization', 'sql']
                test_engineer_keywords = ['software test engineer', 'qa engineer', 'automation testing', 'manual testing', 'selenium', 'junit']
                db_admin_keywords = ['database administrator', 'db admin', 'sql server', 'mysql', 'oracle', 'database management']
                it_manager_keywords = ['information technology manager', 'it manager', 'it operations', 'it service management', 'project management']

                for skill in resume_data['skills']:
                    skill_lower = skill.lower()
                    if skill_lower in ds_keyword:
                        reco_field = 'Data Science'
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling', 'Data Mining', 'Clustering & Classification', 'Data Analytics', 'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras', 'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask", 'Streamlit']
                        break
                    elif skill_lower in web_keyword:
                        reco_field = 'Web Development'
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento', 'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        break
                    elif skill_lower in android_keyword:
                        reco_field = 'Android Development'
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java', 'Kivy', 'GIT', 'SDK', 'SQLite']
                        break
                    elif skill_lower in ios_keyword:
                        reco_field = 'IOS Development'
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode', 'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation', 'Auto-Layout']
                        break
                    elif skill_lower in uiux_keyword:
                        reco_field = 'UI-UX Development'
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq', 'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing', 'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe', 'Solid', 'Grasp', 'User Research']
                        break
                    elif skill_lower in java_dev_keywords:
                        reco_field = 'Java Developer'
                        recommended_skills = ['Java', 'JDK', 'Spring', 'Hibernate', 'Maven', 'Gradle', 'RESTful APIs', 'Microservices', 'Unit Testing', 'Integration Testing']
                        break
                    elif skill_lower in dev_ops_manager_keywords:
                        reco_field = 'Development Operations Manager'
                        recommended_skills = ['DevOps', 'Continuous Integration', 'Continuous Deployment', 'Docker', 'Kubernetes', 'Jenkins', 'Infrastructure as Code']
                        break
                    elif skill_lower in it_security_keywords:
                        reco_field = 'IT Security Specialist'
                        recommended_skills = ['Cybersecurity', 'Network Security', 'Information Security', 'Firewall Management', 'Penetration Testing', 'Security Audits']
                        break
                    elif skill_lower in application_analyst_keywords:
                        reco_field = 'Application Analyst'
                        recommended_skills = ['Application Support', 'Business Analysis', 'Requirements Gathering', 'Software Documentation', 'Problem-Solving']
                        break
                    elif skill_lower in bi_analyst_keywords:
                        reco_field = 'Business Intelligence Analyst'
                        recommended_skills = ['Business Intelligence', 'Data Analysis', 'Data Visualization Tools', 'SQL', 'ETL Processes', 'Dashboard Design']
                        break
                    elif skill_lower in test_engineer_keywords:
                        reco_field = 'Software Test Engineer'
                        recommended_skills = ['Manual Testing', 'Automation Testing', 'Selenium', 'JUnit', 'Test Planning', 'Bug Tracking']
                        break
                    elif skill_lower in db_admin_keywords:
                        reco_field = 'Database Administrator'
                        recommended_skills = ['SQL Server', 'MySQL', 'Oracle', 'Database Tuning', 'Backup & Recovery', 'Database Security']
                        break
                    elif skill_lower in it_manager_keywords:
                        reco_field = 'Information Technology Manager'
                        recommended_skills = ['IT Operations', 'Project Management', 'IT Service Management', 'Leadership', 'Budgeting', 'Vendor Management']
                        break


                if reco_field:
                    st.subheader(f"**Recommended Field: {reco_field}**")
                    st.subheader("**Recommended Skills to Add**")
                    for skill in recommended_skills:
                        st.write(skill)

                    recommended_jobs = recommend_jobs(reco_field, resume_data['skills'])
                    if recommended_jobs:
                        st.subheader("**Recommended Jobs**")
                        for idx, job in enumerate(recommended_jobs[:10], start=1):
                            st.write(f"**Rank {idx}**")
                            st.write(f"**Title**: {job['Title']}")
                            st.write(f"**Company**: {job['Company']}")
                            st.write(f"**Location**: {job['Location']}")
                            st.write(f"**Job URL**: [Link]({job['Job URL']})")
                            st.write(f"**Matched Skills**: {', '.join(job['Matched Skills'])}")
                            st.write("---")

if __name__ == '__main__':
    run()
