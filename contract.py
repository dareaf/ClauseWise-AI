import streamlit as st
from PyPDF2 import PdfReader
import json
import re
import google.generativeai as google_ai
import re
import json

google_ai.configure(api_key='AIzaSyBiymSeFOky24cEw9hA_CcOT-ULMGOE43Y')
model = google_ai.GenerativeModel('gemini-pro')

PAGE_CONFIG = {"page_title":"ClauseWise", 
               "layout":"centered", 
               "initial_sidebar_state":"auto",
                "page_icon":"🛡️",
               }

st.set_page_config(**PAGE_CONFIG)

def call_google_gemini_ai(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        st.error(f"Error calling Google Generative AI: {str(e)}")
        return None

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def detect_contract_type(contract_text):
    prompt = f"""
    Analyze the following contract text and determine the type of contract it is.
    Provide only the contract type as a single string (e.g., "Employment", "Non-Disclosure Agreement", "Sales", "Lease", etc.).
    Do not include any additional explanation or text.
    
    Contract text:
    {contract_text[:2000]}
    """
    response_text = call_google_gemini_ai(prompt)
    
    if response_text:
        return response_text.strip()
    else:
        return "Unknown Contract Type"

def clean_and_parse_json(text):
    text = re.sub(r"```json\n?|\n?```", "", text).strip()

    try:
        text = re.sub(r'/([{,]\s*)(\w+)(\s*:)/g', r'\1"\2"\3', text)
        text = re.sub(r'/:\s*"([^"]*)"([^,}\]])/g', r': "$1"$2', text)
        text = re.sub(r',\s*}/g', '}', text)
        
        analysis = json.loads(text)
        return analysis

    except json.JSONDecodeError as error:
        print(f"Error parsing JSON: {error}")
        return None

def analyze_contract_with_ai(contract_text, tier, contract_type):
    if tier == "premium":
        prompt = f'''
            Analyze the following {contract_type} contract and provide:
            1. A list of at least 10 potential risks for the party receiving the contract, each with a brief explanation and severity level (low, medium, high).
            2. A list of at least 10 potential opportunities or benefits for the receiving party, each with a brief explanation and impact level (low, medium, high).
            3. A comprehensive summary of the contract, including key terms and conditions.
            4. Any recommendations for improving the contract from the receiving party's perspective.
            5. A list of key clauses in the contract.
            6. An assessment of the contract's legal compliance.
            7. A list of potential negotiation points.
            8. The contract duration or term, if applicable.
            9. A summary of termination conditions, if applicable.
            10. A breakdown of any financial terms or compensation structure, if applicable.
            11. Any performance metrics or KPIs mentioned, if applicable.
            12. A summary of any specific clauses relevant to this type of contract (e.g., intellectual property for employment contracts, warranties for sales contracts).
            13. An overall score from 1 to 100, with 100 being the highest. This score represents the overall favorability of the contract based on the identified risks and opportunities.

            Format your response as a JSON object with the following structure:
            {{
            "risks": [
                {{
                "risk": "Risk description", 
                "explanation": "Brief explanation", 
                "severity": "low|medium|high"
                }}
            ],
            "opportunities": [
                {{
                "opportunity": "Opportunity description", 
                "explanation": "Brief explanation", 
                "impact": "low|medium|high"
                }}
            ],
            "summary": "Comprehensive summary of the contract",
            "recommendations": ["Recommendation 1", "Recommendation 2", "..."],
            "keyClauses": ["Clause 1", "Clause 2", "..."],
            "legalCompliance": "Assessment of legal compliance",
            "negotiationPoints": ["Point 1", "Point 2", "..."],
            "contractDuration": "Duration of the contract, if applicable",
            "terminationConditions": "Summary of termination conditions, if applicable",
            "overallScore": "Overall score from 1 to 100",
            "financialTerms": {{
                "description": "Overview of financial terms",
                "details": ["Detail 1", "Detail 2", "..."]
            }},
            "performanceMetrics": ["Metric 1", "Metric 2", "..."],
            "specificClauses": "Summary of clauses specific to this contract type"
            }}

            Contract text:
            {contract_text}
            '''
    else:
        prompt = f'''
            Analyze the following {contract_type} contract and provide:
            1. A list of at least 5 potential risks for the party receiving the contract, each with a brief explanation and severity level (low, medium, high).
            2. A list of at least 5 potential opportunities or benefits for the receiving party, each with a brief explanation and impact level (low, medium, high).
            3. A brief summary of the contract.
            4. An overall score from 1 to 100, with 100 being the highest. This score represents the overall favorability of the contract based on the identified risks and opportunities.

            Format your response as a JSON object with the following structure:
            {{
            "risks": [
                {{
                "risk": "Risk description", 
                "explanation": "Brief explanation", 
                "severity": "low|medium|high"
                }}
            ],
            "opportunities": [
                {{
                "opportunity": "Opportunity description", 
                "explanation": "Brief explanation", 
                "impact": "low|medium|high"
                }}
            ],
            "summary": "Brief summary of the contract",
            "overallScore": "Overall score from 1 to 100"
            }}

            Contract text:
            {contract_text}
            '''
    
    prompt += "Important: Provide only the JSON object in your response, without any additional text or formatting."
    
    ai_response_text = call_google_gemini_ai(prompt)
    analysis = clean_and_parse_json(ai_response_text)
    return analysis

st.markdown("<h1 style='text-align: center; font-family: Arial;'>🛡️</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; font-family: italic;'><span style='color: #6f42c1;'>Clause</span>Wise <span style='background: linear-gradient(to right, #007BFF, #28a745); -webkit-background-clip: text; color: transparent;'>AI</span></h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; font-family: Courier New;'>AI powered contract analysis</h4>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload a contract", type="pdf")

if uploaded_file:
    pdf_text = extract_text_from_pdf(uploaded_file)
    detected_type = detect_contract_type(pdf_text)
    st.write(f"Detected Contract Type: {detected_type}")
    user_type = st.radio("Select User Type", ("Free", "Premium"))
    
    if st.button("Analyze Contract"):
        try:
            analysis = analyze_contract_with_ai(pdf_text, user_type.lower(), detected_type)
            
            if analysis:
                st.write("### Contract Analysis Results")
                st.write(f"**Summary:** {analysis.get('summary', 'No summary available')}")
                st.write(f"**Risks:** {analysis.get('risks', [])}")
                st.write(f"**Opportunities:** {analysis.get('opportunities', [])}")
                st.write(f"**Key Clauses:** {analysis.get('keyClauses', [])}")
                st.write(f"**Overall Score:** {analysis.get('overallScore', 'No score available')}")
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
