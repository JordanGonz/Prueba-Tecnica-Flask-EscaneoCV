from datetime import datetime
from app import db

class Candidate(db.Model):
    """Candidate model for storing CV information and extracted data"""
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    
    # Professional Information
    education = db.Column(db.Text)  # JSON string of education details
    experience = db.Column(db.Text)  # JSON string of experience details
    skills = db.Column(db.Text)  # JSON string of skills
    
    # CV Content
    full_text = db.Column(db.Text, nullable=False)  # Complete CV text
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # pdf, docx, txt
    
    # AI Analysis Results
    vision_analysis = db.Column(db.Text)  # JSON string from OpenAI Vision analysis
    text_embedding = db.Column(db.Text)  # JSON array of embedding vector
    
    # Additional extracted fields
    languages = db.Column(db.Text)  # JSON string of languages
    certifications = db.Column(db.Text)  # JSON string of certifications
    summary = db.Column(db.Text)  # Professional summary
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Candidate {self.name}>'
    
    def to_dict(self):
        """Convert candidate to dictionary for easy JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'education': self.education,
            'experience': self.experience,
            'skills': self.skills,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
