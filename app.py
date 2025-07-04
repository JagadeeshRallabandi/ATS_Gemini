import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
import docx2txt
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

safety_settings = [
    {"category": f"HARM_CATEGORY_{category}", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    for category in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]
]


# LLM Generation
def generate_response_from_gemini(input_text):
    llm = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    output = llm.generate_content(input_text)
    return output.text

# File extractors
def extract_text_from_pdf_file(uploaded_file):
    pdf_reader = pdf.PdfReader(uploaded_file)
    text_content = ""
    for page in pdf_reader.pages:
        text_content += str(page.extract_text())
    return text_content

def extract_text_from_docx_file(uploaded_file):
    return docx2txt.process(uploaded_file)

# Prompt Template
input_prompt_template = """
As an experienced Applicant Tracking System (ATS) analyst,
with profound knowledge in technology, software engineering, data science,
and big data engineering, your role involves evaluating resumes against job descriptions.
Recognizing the competitive job market, provide top-notch assistance for resume improvement.
Your goal is to analyze the resume against the given job description,
assign a percentage match based on key criteria, and pinpoint missing keywords accurately.

resume:{text}
description:{job_description}
I want the response in one single string having the structure
{{"Job Description Match": "%","Missing Keywords":"","Candidate Summary":"","Experience":""}}
"""

# Streamlit UI
st.title("Intelligent ATS - Enhance Your Resume for Job Matching")

job_description = st.text_area("Paste the Job Description", height=300)
uploaded_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx"], help="Please upload a PDF or DOCX file")
submit_button = st.button("Submit")

if submit_button:
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf_file(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            resume_text = extract_text_from_docx_file(uploaded_file)

        formatted_prompt = input_prompt_template.format(
            text=resume_text,
            job_description=job_description
        )
        
        response_text = generate_response_from_gemini(formatted_prompt)

        st.subheader("ATS Evaluation Result:")
        st.write(response_text)

        # Optional: Try parsing match percentage if it's present
        try:
            import re
            match = re.search(r'"Job Description Match"\s*:\s*"(\d+)%', response_text)
            if match:
                match_percentage = int(match.group(1))
                if match_percentage >= 80:
                    st.success("✅ Match! Move forward with hiring.")
                else:
                    st.warning("❌ Not a Match.")
        except:
            st.warning("Couldn't parse match percentage.")
