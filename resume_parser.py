from typing import Dict
import PyPDF2
import docx2txt
import re
from pathlib import Path

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        return docx2txt.process(file_path)
    except Exception as e:
        print(f"Error reading DOCX: {str(e)}")
        return ""

def extract_email(text: str) -> str:
    """Extract email address from text."""
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""

def extract_name(text: str) -> str:
    """Extract candidate name from text."""
    # Simple heuristic: first line is often the name
    lines = text.split('\n')
    for line in lines:
        if line.strip() and not any(char.isdigit() for char in line):
            return line.strip()
    return ""

def extract_education(text: str) -> str:
    """Extract education information from text."""
    education_keywords = ['education', 'academic', 'degree', 'university', 'college', 'bachelor', 'master', 'phd']
    lines = text.split('\n')
    education = []
    
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in education_keywords):
            # Include the current line and next few lines
            education.extend(lines[i:i+5])
    
    return '\n'.join(education)

def extract_skills(text: str) -> list:
    """Extract skills from text."""
    # Common technical skills to look for
    common_skills = [
        'python', 'java', 'javascript', 'sql', 'html', 'css', 'react', 'angular',
        'node.js', 'aws', 'azure', 'docker', 'kubernetes', 'git', 'linux',
        'machine learning', 'data analysis', 'project management'
    ]
    
    found_skills = []
    for skill in common_skills:
        if skill in text.lower():
            found_skills.append(skill)
    
    return found_skills

def parse_resume(file_path: str) -> Dict:
    """
    Extracts key information from resumes and returns a structured output.
    
    Args:
        file_path (str): Path to the resume file (PDF or DOCX)
        
    Returns:
        Dict: Structured resume data containing name, email, education, skills, and experience
    """
    try:
        # Determine file type and extract text
        file_extension = Path(file_path).suffix.lower()
        if file_extension == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            text = extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Please provide PDF or DOCX.")
        
        # Extract information
        return {
            "name": extract_name(text),
            "email": extract_email(text),
            "education": extract_education(text),
            "skills": extract_skills(text),
            "experience": text  # For now, return full text as experience
        }
        
    except Exception as e:
        print(f"Error parsing resume: {str(e)}")
        return {
            "name": "",
            "email": "",
            "education": "",
            "skills": [],
            "experience": ""
        } 