from fastapi import FastAPI, UploadFile, File, Form, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from services.job_description_processor import JobDescriptionProcessor
from services.resume_parser import ResumeParser
from services.candidate_matcher import CandidateMatcher
from services.interview_scheduler import InterviewScheduler
from database.models import JobDescription, Resume, ShortlistedCandidate, InterviewSchedule
from database.database import SessionLocal, engine
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from datetime import datetime
import json
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import func
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Create database tables
JobDescription.metadata.create_all(bind=engine)
Resume.metadata.create_all(bind=engine)
ShortlistedCandidate.metadata.create_all(bind=engine)
InterviewSchedule.metadata.create_all(bind=engine)

app = FastAPI(title="RecruitAI API", description="AI-powered recruitment automation system")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# API Models
class JobDescriptionInput(BaseModel):
    text: Optional[str] = None

class JobDescriptionResponse(BaseModel):
    id: int
    title: str
    description: str
    requirements: str
    file_path: Optional[str] = None

class ResumeResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    skills: str
    experience: str
    education: str
    file_path: Optional[str] = None

class MatchRequest(BaseModel):
    job_id: int
    candidate_id: int

class MatchResponse(BaseModel):
    job_id: int
    candidate_id: int
    match_score: float
    shortlisted: bool

class InterviewRequest(BaseModel):
    job_id: int
    candidate_id: int
    interview_date: str
    interview_time: str

class InterviewResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    scheduled_time: datetime
    sent_email: bool

@app.get("/")
async def read_root():
    return {"message": "RecruitAI API - AI-powered recruitment automation system"}

@app.post("/api/upload-jd")
async def upload_jd(
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        # Check if either text or file is provided
        if not jd_text and not jd_file:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "detail": "Please provide either job description text or a file"}
            )

        # Handle text input
        if jd_text:
            # Save text to temp file
            temp_file_path = f"uploads/jd_text_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            with open(temp_file_path, "w") as f:
                f.write(jd_text)
            file_path = temp_file_path
        else:
            # Handle file upload
            file_path = f"uploads/{jd_file.filename}"
            with open(file_path, "wb") as buffer:
                content = await jd_file.read()
                buffer.write(content)

        # Process the job description
        processor = JobDescriptionProcessor()
        summary = processor.process(file_path)

        # Save to database
        job = JobDescription(
            title=summary.get("title", "Untitled"),
            description=summary.get("description", ""),
            requirements=summary.get("requirements", ""),
            file_path=file_path
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        return {
            "status": "success", 
            "message": "Job description processed successfully",
            "job_id": job.id,
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

@app.post("/api/upload-resume")
async def upload_resume(
    resume_files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    try:
        results = []
        for resume_file in resume_files:
            # Save the uploaded file
            file_path = f"uploads/{resume_file.filename}"
            with open(file_path, "wb") as buffer:
                content = await resume_file.read()
                buffer.write(content)

            # Parse the resume
            parser = ResumeParser()
            resume_data = parser.parse(file_path)

            # Save to database
            resume = Resume(
                name=resume_data.get("name", "Unknown"),
                email=resume_data.get("email", ""),
                phone=resume_data.get("phone", ""),
                skills=", ".join(resume_data.get("skills", [])),
                experience=resume_data.get("experience", ""),
                education=resume_data.get("education", ""),
                file_path=file_path
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)
            
            # Add to results
            results.append({
                "id": resume.id,
                "name": resume.name,
                "email": resume.email,
                "phone": resume.phone,
                "skills": resume.skills,
                "experience": resume.experience,
                "education": resume.education
            })

        return {"status": "success", "message": f"{len(results)} resume(s) processed successfully", "resumes": results}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

@app.post("/api/match")
async def match_candidate(
    request: MatchRequest,
    db: Session = Depends(get_db)
):
    try:
        job = db.query(JobDescription).filter(JobDescription.id == request.job_id).first()
        candidate = db.query(Resume).filter(Resume.id == request.candidate_id).first()

        if not job or not candidate:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "detail": "Job or candidate not found"}
            )

        matcher = CandidateMatcher()
        match_score = matcher.calculate_match_score(job, candidate)

        # Save to shortlisted candidates if score is high enough
        shortlisted = match_score >= 80
        if shortlisted:
            # Check if already shortlisted
            existing = db.query(ShortlistedCandidate).filter(
                ShortlistedCandidate.job_id == request.job_id,
                ShortlistedCandidate.candidate_id == request.candidate_id
            ).first()
            
            if not existing:
                shortlisted_candidate = ShortlistedCandidate(
                    job_id=request.job_id,
                    candidate_id=request.candidate_id,
                    match_score=match_score
                )
                db.add(shortlisted_candidate)
                db.commit()

        return {
            "status": "success", 
            "job_id": request.job_id,
            "candidate_id": request.candidate_id,
            "match_score": match_score,
            "shortlisted": shortlisted
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

@app.post("/api/schedule-interview")
async def schedule_interview(
    request: InterviewRequest,
    db: Session = Depends(get_db)
):
    try:
        job = db.query(JobDescription).filter(JobDescription.id == request.job_id).first()
        candidate = db.query(Resume).filter(Resume.id == request.candidate_id).first()

        if not job or not candidate:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "detail": "Job or candidate not found"}
            )

        # Parse date and time
        interview_datetime_str = f"{request.interview_date} {request.interview_time}"
        interview_datetime = datetime.strptime(interview_datetime_str, "%Y-%m-%d %H:%M")

        # Save to database
        interview = InterviewSchedule(
            job_id=request.job_id,
            candidate_id=request.candidate_id,
            scheduled_time=interview_datetime
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)

        # Send a dummy email (in a real scenario, you would use a proper email service)
        try:
            # Dummy email function that doesn't actually send anything
            send_interview_invitation(candidate.email, candidate.name, job.title, interview_datetime)
            email_sent = True
        except Exception as email_error:
            print(f"Error sending email: {str(email_error)}")
            email_sent = False

        return {
            "status": "success",
            "message": "Interview scheduled successfully",
            "interview_id": interview.id,
            "scheduled_time": interview.scheduled_time,
            "email_sent": email_sent
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

# Get all job descriptions
@app.get("/api/jobs")
async def get_jobs(db: Session = Depends(get_db)):
    try:
        jobs = db.query(JobDescription).all()
        job_list = []
        for job in jobs:
            job_list.append({
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "requirements": job.requirements
            })
        return {"status": "success", "jobs": job_list}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

# Get all resumes/candidates
@app.get("/api/candidates")
async def get_candidates(db: Session = Depends(get_db)):
    try:
        candidates = db.query(Resume).all()
        candidate_list = []
        for candidate in candidates:
            candidate_list.append({
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "phone": candidate.phone,
                "skills": candidate.skills,
                "experience": candidate.experience,
                "education": candidate.education
            })
        return {"status": "success", "candidates": candidate_list}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

# Get shortlisted candidates for a job
@app.get("/api/shortlisted/{job_id}")
async def get_shortlisted(job_id: int, db: Session = Depends(get_db)):
    try:
        # Get job details
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "detail": "Job not found"}
            )
            
        # Get shortlisted candidates
        shortlisted_query = db.query(
            ShortlistedCandidate, Resume
        ).join(
            Resume, ShortlistedCandidate.candidate_id == Resume.id
        ).filter(
            ShortlistedCandidate.job_id == job_id
        ).order_by(
            ShortlistedCandidate.match_score.desc()
        ).all()
        
        shortlisted_list = []
        for shortlisted, candidate in shortlisted_query:
            shortlisted_list.append({
                "id": shortlisted.id,
                "job_id": shortlisted.job_id,
                "candidate_id": shortlisted.candidate_id,
                "match_score": shortlisted.match_score,
                "candidate_name": candidate.name,
                "candidate_email": candidate.email,
                "candidate_skills": candidate.skills
            })
            
        return {
            "status": "success", 
            "job": {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "requirements": job.requirements
            },
            "shortlisted": shortlisted_list
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

# Get scheduled interviews
@app.get("/api/interviews")
async def get_interviews(db: Session = Depends(get_db)):
    try:
        interviews_query = db.query(
            InterviewSchedule, JobDescription, Resume
        ).join(
            JobDescription, InterviewSchedule.job_id == JobDescription.id
        ).join(
            Resume, InterviewSchedule.candidate_id == Resume.id
        ).all()
        
        interview_list = []
        for interview, job, candidate in interviews_query:
            interview_list.append({
                "id": interview.id,
                "job_id": interview.job_id,
                "candidate_id": interview.candidate_id,
                "scheduled_time": interview.scheduled_time,
                "job_title": job.title,
                "candidate_name": candidate.name,
                "candidate_email": candidate.email
            })
            
        return {"status": "success", "interviews": interview_list}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

# Function to send interview invitation (dummy implementation)
def send_interview_invitation(email, name, job_title, interview_datetime):
    # In a real-world application, you'd use SMTP or an email service
    # This is a dummy implementation that just logs the message
    print(f"Sending interview invitation to {name} <{email}>")
    print(f"Job: {job_title}")
    print(f"Scheduled time: {interview_datetime.strftime('%Y-%m-%d %H:%M')}")
    
    # For a real implementation, you'd do something like:
    '''
    message = MIMEMultipart()
    message["From"] = "recruiter@company.com"
    message["To"] = email
    message["Subject"] = f"Interview Invitation for {job_title} position"
    
    body = f"""
    Hello {name},
    
    We're pleased to invite you for an interview for the {job_title} position.
    
    Date: {interview_datetime.strftime('%A, %B %d, %Y')}
    Time: {interview_datetime.strftime('%I:%M %p')}
    
    Please confirm your availability for this interview.
    
    Best regards,
    Recruitment Team
    """
    
    message.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("your-email@gmail.com", "your-password")
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False
    '''
    
    # Just return True for the dummy implementation
    return True

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 