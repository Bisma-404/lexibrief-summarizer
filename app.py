import streamlit as st
from transformers import pipeline
from PyPDF2 import PdfReader
import os
import base64
st.set_page_config(
    page_title="LexiBrief - AI Summarizer",
    layout="wide"
)

def inject_css():
    st.markdown("""
    <style>
        :root {
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --text: #2d3748;
            --text-muted: #64748b;
            --bg: #ffffff;
            --card-bg: #ffffff;
            --card-border: #e2e8f0;
        }
        
        [data-testid="stAppViewContainer"] {
            background-color: #f9fafb;
        }
        
        .header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            padding: 15px 0;
            border-bottom: 1px solid var(--card-border);
        }
        
        .logo {
            width: 60px;
            height: 60px;
            object-fit: contain;
        }
        
        .title {
            font-size: clamp(24px, 5vw, 32px);
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0;
        }
        
        .description {
            font-size: clamp(14px, 3vw, 16px);
            color: var(--text-muted);
            margin-top: 4px;
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: clamp(15px, 3vw, 25px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            border: 1px solid var(--card-border);
            margin-bottom: clamp(15px, 3vw, 25px);
        }
        
        .stButton>button {
            background-color: var(--primary);
            color: white;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.2s;
            border: none;
            width: 100%;
        }
        
        .stButton>button:hover {
            background-color: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .stTextArea textarea {
            min-height: 200px;
            border-radius: 8px;
            width: 100% !important;
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                text-align: center;
                gap: 10px;
            }
            
            .stColumn {
                width: 100% !important;
                padding: 0 !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

inject_css()

@st.cache_resource
def load_summarizer():
    try:
        return pipeline("summarization", 
                      model="facebook/bart-large-cnn",
                      device="cpu")
    except Exception as e:
        st.error(f"Failed to load summarizer: {str(e)}")
        return None

def get_image_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"Couldn't load logo: {str(e)}")
        return ""

logo_base64 = get_image_base64("lexibrief_logo.png") or ""
st.markdown(f"""
<div class="header">
    <img src="data:image/png;base64,{logo_base64}" class="logo" onerror="this.style.display='none'">
    <div>
        <h1 class="title">LexiBrief</h1>
        <p class="description">AI-powered text and document summarization for professionals</p>
    </div>
</div>
""", unsafe_allow_html=True)

def extract_text_from_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            return text.strip()
    except Exception as e:
        st.error(f"PDF processing error: {str(e)}")
        return ""

# Sidebar navigation
with st.sidebar:
    st.markdown("## Navigation")
    choice = st.radio(
        "Select mode",
        ["Summarize Text", "Summarize Document"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("""
    <div style='color: var(--text-muted); font-size: 14px;'>
        <p>LexiBrief uses advanced AI to extract key insights from your content.</p>
        <p>Max PDF size: 10MB</p>
    </div>
    """, unsafe_allow_html=True)

summarizer = load_summarizer()

if choice == "Summarize Text":
    with st.container():
        st.markdown("### Text Summarization")
        with st.form("text_form"):
            input_text = st.text_area(
                "Enter your text here",
                height=250,
                placeholder="Paste your content here..."
            )
            
            if st.form_submit_button("Generate Summary"):
                if input_text.strip():
                    if summarizer is None:
                        st.error("Summarization engine not available")
                    else:
                        with st.spinner("Generating summary..."):
                            try:
                                result = summarizer(
                                    input_text,
                                    max_length=150,
                                    min_length=50,
                                    do_sample=False
                                )[0]['summary_text']
                                
                                col1, col2 = st.columns([1,1])
                                with col1:
                                    with st.container():
                                        st.markdown("#### Original Text")
                                        st.info(input_text)
                                with col2:
                                    with st.container():
                                        st.markdown("#### Summary Result")
                                        st.success(result)
                            except Exception as e:
                                st.error(f"Summarization failed: {str(e)}")
                else:
                    st.warning("Please enter some text to summarize")

elif choice == "Summarize Document":
    with st.container():
        st.markdown("### Document Summarization")
        with st.form("doc_form"):
            input_file = st.file_uploader(
                "Upload your PDF document (max 10MB)",
                type=['pdf'],
                accept_multiple_files=False
            )
            
            if st.form_submit_button("Summarize Document") and input_file is not None:
                if input_file.size > 10_000_000:  
                    st.error("Please upload PDFs smaller than 10MB")
                elif summarizer is None:
                    st.error("Summarization engine not available")
                else:
                    temp_file = "temp_doc.pdf"
                    try:
                        with open(temp_file, "wb") as f:
                            f.write(input_file.getbuffer())
                        
                        with st.spinner("Processing document..."):
                            extracted_text = extract_text_from_pdf(temp_file)
                            
                            if extracted_text:
                                try:
                                    summary = summarizer(
                                        extracted_text,
                                        max_length=150,
                                        min_length=50,
                                        do_sample=False
                                    )[0]['summary_text']
                                    
                                    col1, col2 = st.columns([1,1])
                                    with col1:
                                        with st.container():
                                            st.markdown("#### Extracted Text")
                                            st.info(extracted_text[:2000] + "..." if len(extracted_text) > 2000 else extracted_text)
                                    with col2:
                                        with st.container():
                                            st.markdown("#### Summary Result")
                                            st.success(summary)
                                except Exception as e:
                                    st.error(f"Summarization failed: {str(e)}")
                            else:
                                st.error("No text could be extracted from the document")
                    except Exception as e:
                        st.error(f"File processing error: {str(e)}")
                    finally:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)


st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: var(--text-muted); padding: 20px;">
        <p>Developed by Bisma Shahid</p>
    </div>
    """,
    unsafe_allow_html=True
)