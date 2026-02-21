import os
import requests
from pypdf import PdfReader
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

def extract_resume_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def get_llm_response(prompt, system_prompt):
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY not found in .env"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error calling OpenAI: {e}"
            
    else: # Default to Ollama
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        url = f"{base_url}/api/chat"
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            return f"Error calling Ollama: {e}"

class InterviewPDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 15)
        self.cell(0, 10, "Technical Interview Conversation Loop", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')

def generate_pdf(content, output_path):
    pdf = InterviewPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Replace common unicode characters that FPDF1/2 standard fonts don't support
    content = content.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, content)
    pdf.output(output_path)

def main():
    print("Extracting resume...")
    resume_text = extract_resume_text("Resume.pdf")
    if not resume_text:
        return

    system_prompt = "You are an expert technical interviewer for FAANG-level Python/Django roles. Create a realistic, high-quality interview conversation loop based on the user's resume."
    
    prompt = f"""
Based on the following resume:
---
{resume_text}
---

Generate a conversation-style technical interview loop. 
Format it as a dialogue between 'Interviewer' and 'Candidate'.
Focus on:
1. Python/Django deep dives (MFA, Celery, Query Optimization).
2. Real-world scenarios (dealing with legacy code, scaling APIs).
3. Trade-offs and performance (PostgreSQL vs Redis).
4. VAPT and security.

Provide about 10 questions and detailed answers from the candidate.
Make the candidate sound like the person in the resume (Aakash Vats).
"""

    print("Calling LLM to generate interview loop...")
    interview_content = get_llm_response(prompt, system_prompt)
    
    if interview_content.startswith("Error"):
        print(interview_content)
        return

    print("Generating PDF...")
    generate_pdf(interview_content, "Interview_Loop.pdf")
    print("Done! Interview_Loop.pdf has been generated in the current folder.")

if __name__ == "__main__":
    main()
