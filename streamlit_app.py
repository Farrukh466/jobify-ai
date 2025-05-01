import streamlit as st
import pickle
import os
import docx2txt
import PyPDF2
import io
import requests

st.set_page_config(page_title="AI Resume Classifier & Job Recommender", page_icon="💼", layout="wide")

# Custom CSS for file uploader
st.markdown(
    """
    <style>
    .stFileUploader > label div[data-testid="stFileUploaderDropzone"] {
        background-color: #4CAF50;
        color: white;
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        transition: 0.3s;
    }
    .stFileUploader > label div[data-testid="stFileUploaderDropzone"]:hover {
        background-color: #45a049;
        border-color: #45a049;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def extract_text(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return docx2txt.process(io.BytesIO(file.read()))
    return None

@st.cache_resource
def load_models():
    vectorizer_path = 'saved_models/vectorizer.pkl'
    vectorizer = pickle.load(open(vectorizer_path, 'rb'))
    model_dir = 'saved_models'
    model_files = [f for f in os.listdir(model_dir) if f.endswith('.pkl') and f != 'vectorizer.pkl']
    models = {}
    for file in model_files:
        model_name = file.replace('.pkl', '')
        with open(os.path.join(model_dir, file), 'rb') as f:
            models[model_name] = pickle.load(f)
    return vectorizer, models

vectorizer, models = load_models()

def search_jobs(params):
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": "3928ef76dbmsh3fdca79a275933dp15f5c5jsn5c4c2152e54b",
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("data", [])
            if not jobs:
                st.warning("⚠️ No jobs found for the specified criteria. Try a different location, broader date range, or fewer filters.")
            return [job for job in jobs if job is not None]
        else:
            st.error(f"❌ Error fetching jobs: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"❌ API call failed: {str(e)}")
        return []


if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'prediction' not in st.session_state:
    st.session_state.prediction = None
if 'location' not in st.session_state:
    st.session_state.location = ""

if not st.session_state.selected_job:
    st.markdown("<h3 style='text-align: center; margin-top: 20px;margin-bottom: 20px;'>AI Resume Classifier & Job Recommender</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader("📤 Upload your resume (.pdf or .docx)", type=["pdf", "docx"])
    with col2:
        model_options = list(models.keys())
        selected_model = st.selectbox("🧠 Select prediction model", model_options)

    if uploaded_file and selected_model:
        resume_text = extract_text(uploaded_file)
        if resume_text:
            model = models[selected_model]
            transformed = vectorizer.transform([resume_text])
            prediction = model.predict(transformed)[0]
            st.session_state.prediction = prediction
            st.success(f"✅ **Predicted Job Category:** {prediction}")

            # Location Input
            st.session_state.location = st.text_input("📍 Enter job location (e.g., New York, Karachi)", value=st.session_state.location)

            # Job Search Parameters Form with Two-Column Layout
            st.markdown("<h4 style='margin-top: 20px;'>Configure Additional Job Search Parameters</h4>", unsafe_allow_html=True)
            with st.form(key="job_search_form"):
                col_left, col_right = st.columns(2)
                
                # Left Column: num_pages, work_from_home, job_requirements
                with col_left:
                    num_pages = st.slider("📚 Number of Pages", min_value=1, max_value=20, value=1)
                    work_from_home = st.checkbox("🏠 Remote/Work from Home Only", value=False)
                    job_requirements = st.multiselect(
                        "📋 Job Requirements",
                        ["under_3_years_experience", "more_than_3_years_experience", "no_experience", "no_degree"],
                        default=[],
                        key="job_requirements"
                    )
                
                # Right Column: date_posted, employment_types, country
                with col_right:
                    date_posted = st.selectbox("🕒 Jobs Posted Within", ["all", "today", "3days", "week", "month"], index=0)
                    employment_types = st.multiselect(
                        "💼 Employment Types",
                        ["FULLTIME", "CONTRACTOR", "PARTTIME", "INTERN"],
                        default=["FULLTIME"],
                        key="employment_types"
                    )
                    country = st.text_input("🌍 Country Code (e.g., us, pk)", value="us")
                
                # Submit button centered below columns
                st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
                submit_button = st.form_submit_button("🔎 Search Jobs")
                st.markdown("</div>", unsafe_allow_html=True)

            if submit_button:
                if not st.session_state.location.strip():
                    st.warning("⚠️ Please enter a job location.")
                elif not country.strip():
                    st.warning("⚠️ Please enter a country code.")
                else:
                    # Construct API parameters
                    params = {
                        "query": f"{prediction} jobs in {st.session_state.location.strip()}",
                        "page": "1",
                        "num_pages": str(num_pages),
                        "country": country.strip(),
                        "date_posted": date_posted
                    }
                    if work_from_home:
                        params["work_from_home"] = "true"
                    if employment_types:
                        params["employment_types"] = ",".join(employment_types)
                    if job_requirements:
                        params["job_requirements"] = ",".join(job_requirements)

                    jobs = search_jobs(params)
                    st.session_state.jobs = jobs if jobs else []

        else:
            st.error("❌ Could not extract text from the uploaded resume. Please ensure it's a valid PDF or DOCX file.")

    if st.session_state.jobs:
        st.markdown("<h3 style='margin-top: 20px;'>Jobs for you</h3>", unsafe_allow_html=True)
        col_left, col_right = st.columns(2)
        for idx, job in enumerate(st.session_state.jobs):
            if job is None:
                continue
            if idx % 2 == 0:
                with col_left:
                    with st.container():
                        st.markdown(f"""
                            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 10px; cursor: pointer;">
                                <h4 style="margin: 0;">{job.get('job_title', 'Untitled')}</h4>
                                <p style="margin: 5px 0;">{job.get('employer_name', 'N/A')}</p>
                                <p style="margin: 5px 0;">{job.get('job_city', 'N/A')}</p>
                                <p style="margin: 5px 0; color: #767676;">Rs {job.get('job_min_salary', 'N/A')} - Rs {job.get('job_max_salary', 'N/A')} a month</p>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("Apply now", key=f"apply_{idx}"):
                            st.session_state.selected_job = job
            else:
                with col_right:
                    with st.container():
                        st.markdown(f"""
                            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 10px; cursor: pointer;">
                                <h4 style="margin: 0;">{job.get('job_title', 'Untitled')}</h4>
                                <p style="margin: 5px 0;">{job.get('employer_name', 'N/A')}</p>
                                <p style="margin: 5px 0;">{job.get('job_city', 'N/A')}</p>
                                <p style="margin: 5px 0; color: #767676;">Rs {job.get('job_min_salary', 'N/A')} - Rs {job.get('job_max_salary', 'N/A')} a month</p>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("Apply now", key=f"apply_{idx}"):
                            st.session_state.selected_job = job

else:
    job = st.session_state.selected_job
    if job is None:
        st.error("❌ No job selected. Please go back and select a job.")
        if st.button("Back to job listings"):
            st.session_state.selected_job = None
            st.rerun()
    else:
        st.markdown("<h3>Job details</h3>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 15px;">
                <h4>{job.get('job_title', 'Untitled')}</h4>
                <p><strong>Company:</strong> {job.get('employer_name', 'N/A')}</p>
                <p><strong>Location:</strong> {job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}</p>
                <p><strong>Pay:</strong> Rs {job.get('job_min_salary', 'N/A')} - Rs {job.get('job_max_salary', 'N/A')} a month</p>
                <p><strong>Job type:</strong> {job.get('job_employment_type', 'Full-time')}</p>
                <h5>Description:</h5>
                <p>{job.get('job_description', 'No description available.')}</p>
                <a href="{job.get('job_apply_link', '#')}" target="_blank" style="text-decoration: none;">
                    <button style="padding: 10px 20px; background-color: #2557a7; color: white; border: none; border-radius: 5px; cursor: pointer;">Apply now</button>
                </a>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Back to job listings"):
            st.session_state.selected_job = None
            st.rerun()