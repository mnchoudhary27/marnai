from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    required_skills = Column(String)
    required_experience = Column(String)
    responsibilities = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True)
    candidate_name = Column(String)
    email = Column(String)
    file_path = Column(String)
    education = Column(String)
    skills = Column(String)
    experience = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ShortlistedCandidate(Base):
    __tablename__ = "shortlisted_candidates"
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('resumes.id'))
    job_id = Column(Integer, ForeignKey('job_descriptions.id'))
    match_score = Column(Float)
    status = Column(String)  # pending, scheduled, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    candidate = relationship("Resume")
    job = relationship("JobDescription")

class InterviewSchedule(Base):
    __tablename__ = "interview_schedules"
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('shortlisted_candidates.id'))
    scheduled_time = Column(DateTime)
    status = Column(String)  # pending, confirmed, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    candidate = relationship("ShortlistedCandidate")

# Create database engine
engine = create_engine('sqlite:///recruitment.db')
Base.metadata.create_all(engine) 