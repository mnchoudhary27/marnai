from typing import Dict, List
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class InterviewScheduler:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
    def generate_time_slots(self, start_date: datetime, days: int = 5) -> List[datetime]:
        """Generate available interview time slots."""
        slots = []
        current_date = start_date
        
        for _ in range(days):
            # Generate slots for each day (9 AM to 5 PM, every 1 hour)
            for hour in range(9, 17):
                slot = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                slots.append(slot)
            current_date += timedelta(days=1)
            
        return slots
    
    def send_interview_invite(self, candidate_email: str, match_score: float, time_slot: datetime) -> bool:
        """
        Sends an email with interview scheduling details.
        
        Args:
            candidate_email (str): Candidate's email address
            match_score (float): Match score between candidate and job
            time_slot (datetime): Scheduled interview time
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = candidate_email
            msg['Subject'] = 'Interview Invitation'
            
            # Email body
            body = f"""
            Dear Candidate,
            
            Congratulations! Based on your application, we are pleased to invite you for an interview.
            Your match score with our requirements is {match_score}%.
            
            Interview Details:
            Date: {time_slot.strftime('%Y-%m-%d')}
            Time: {time_slot.strftime('%I:%M %p')}
            
            Please confirm your availability by replying to this email.
            
            Best regards,
            Recruitment Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            print(f"Error sending interview invite: {str(e)}")
            return False
    
    def schedule_interview(self, candidate_data: Dict, match_score: float) -> Dict:
        """
        Schedules an interview for a candidate.
        
        Args:
            candidate_data (Dict): Candidate information
            match_score (float): Match score between candidate and job
            
        Returns:
            Dict: Scheduling result with status and details
        """
        try:
            # Generate time slots starting from tomorrow
            start_date = datetime.now() + timedelta(days=1)
            available_slots = self.generate_time_slots(start_date)
            
            # Select the first available slot
            selected_slot = available_slots[0]
            
            # Send interview invite
            email_sent = self.send_interview_invite(
                candidate_data['email'],
                match_score,
                selected_slot
            )
            
            return {
                'status': 'success' if email_sent else 'failed',
                'scheduled_time': selected_slot.isoformat(),
                'candidate_email': candidate_data['email'],
                'match_score': match_score
            }
            
        except Exception as e:
            print(f"Error scheduling interview: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 