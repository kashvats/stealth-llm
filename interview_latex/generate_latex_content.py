import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_llm_response(prompt):
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        return res.json()["choices"][0]["message"]["content"]
    else:
        url = f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat"
        data = {
            "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        res = requests.post(url, json=data)
        return res.json()["message"]["content"]

def generate_section_3():
    with open("resume_text.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    
    prompt = f"""Continue the professional LaTeX interview bible.
Generate Section 3: System Design & Technical Trade-offs.

Context (Resume):
{resume_text}

Requirements:
1. Discuss system design choices: REST vs GraphQL (if relevant), Monolith vs Microservices.
2. Focus on trade-offs: Caching (Redis) vs Database Hits, PostgreSQL Indexing vs Write Performance.
3. Discuss technical leadership: Mentoring, code reviews, and making architectural decisions.
4. Maintain the Interviewer/Aakash dialogue format.

Format:
\\interviewer{{[Question]}}
\\candidate{{[Answer]}}

ONLY output the LaTeX content for Section 3. Do NOT include preamble, \\begin{{document}}, or \\end{{document}}.
No Markdown code blocks. No meta commentary.
"""
    print("Generating Section 3 content...")
    content = get_llm_response(prompt)
    content = content.replace("```latex", "").replace("```", "").strip()
    
    with open("interview.tex", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if "\\end{document}" not in line:
            new_lines.append(line)
    
    with open("interview.tex", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        f.write("\n\\section*{Section 3: System Design \\& Technical Trade-offs}\n")
        f.write("\\addcontentsline{toc}{section}{Section 3: System Design \\& Technical Trade-offs}\n\n")
        f.write(content)
        f.write("\n\n\\end{document}\n")
    
    print("LaTeX Section 3 appended to interview.tex")

if __name__ == "__main__":
    generate_section_3()
