from typing import Dict
import ollama
from pydantic import BaseModel

class JobDescriptionSummary(BaseModel):
    skills: list[str]
    experience: str
    responsibilities: list[str]
    title: str

def summarize_job_description(jd_text: str) -> Dict:
    """
    Uses Ollama to summarize a job description and return key elements.
    
    Args:
        jd_text (str): The job description text to summarize
        
    Returns:
        Dict: Structured summary containing skills, experience, and responsibilities
    """
    try:
        # Initialize Ollama client
        client = ollama.Client()
        
        # Create a prompt for the LLM
        prompt = f"""
        Analyze the following job description and extract:
        1. Required skills (as a list)
        2. Required experience
        3. Key responsibilities (as a list)
        4. Job title
        
        Format the response as JSON with these keys: skills, experience, responsibilities, title
        
        Job Description:
        {jd_text}
        """
        
        # Get response from Ollama
        response = client.generate(
            model="llama2",
            prompt=prompt,
            format="json"
        )
        
        # Parse the response into a structured format
        summary = JobDescriptionSummary.parse_raw(response.text)
        
        return {
            "skills": summary.skills,
            "experience": summary.experience,
            "responsibilities": summary.responsibilities,
            "title": summary.title
        }
        
    except Exception as e:
        print(f"Error in job description summarization: {str(e)}")
        return {
            "skills": [],
            "experience": "",
            "responsibilities": [],
            "title": ""
        } 