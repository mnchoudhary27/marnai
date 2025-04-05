from typing import Dict
from difflib import SequenceMatcher
import ollama

def calculate_skill_match(jd_skills: list, resume_skills: list) -> float:
    """Calculate skill match percentage."""
    if not jd_skills:
        return 0.0
    
    matched_skills = sum(1 for skill in jd_skills if skill.lower() in [s.lower() for s in resume_skills])
    return (matched_skills / len(jd_skills)) * 100

def calculate_experience_match(jd_experience: str, resume_experience: str) -> float:
    """Calculate experience match using text similarity."""
    if not jd_experience or not resume_experience:
        return 0.0
    
    # Use SequenceMatcher for text similarity
    similarity = SequenceMatcher(None, jd_experience.lower(), resume_experience.lower()).ratio()
    return similarity * 100

def analyze_qualifications(jd_text: str, resume_text: str) -> float:
    """Use Ollama to analyze overall qualifications match."""
    try:
        client = ollama.Client()
        
        prompt = f"""
        Analyze how well the candidate's qualifications match the job requirements.
        Return a score between 0 and 100.
        
        Job Description:
        {jd_text}
        
        Candidate's Experience:
        {resume_text}
        
        Return only the numerical score.
        """
        
        response = client.generate(
            model="llama2",
            prompt=prompt
        )
        
        # Extract numerical score from response
        try:
            score = float(response.text.strip())
            return min(max(score, 0), 100)  # Ensure score is between 0 and 100
        except ValueError:
            return 50.0  # Default score if parsing fails
            
    except Exception as e:
        print(f"Error in qualification analysis: {str(e)}")
        return 50.0

def calculate_match_score(jd_data: Dict, resume_data: Dict) -> float:
    """
    Calculates a match score between a job description and a resume.
    
    Args:
        jd_data (Dict): Job description data
        resume_data (Dict): Resume data
        
    Returns:
        float: Match score out of 100%
    """
    try:
        # Calculate individual component scores
        skill_score = calculate_skill_match(jd_data.get('skills', []), resume_data.get('skills', []))
        experience_score = calculate_experience_match(
            jd_data.get('experience', ''),
            resume_data.get('experience', '')
        )
        
        # Get AI-based qualification analysis
        qualification_score = analyze_qualifications(
            str(jd_data),
            str(resume_data)
        )
        
        # Weighted average of scores
        final_score = (
            skill_score * 0.4 +      # Skills weight: 40%
            experience_score * 0.3 +  # Experience weight: 30%
            qualification_score * 0.3  # Qualifications weight: 30%
        )
        
        return round(final_score, 2)
        
    except Exception as e:
        print(f"Error calculating match score: {str(e)}")
        return 0.0 