from pypdf import PdfReader

try:
    reader = PdfReader("Resume.pdf")
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    with open("resume_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Resume text saved to resume_text.txt")
except Exception as e:
    print(f"Error reading PDF: {e}")
