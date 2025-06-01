import re
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def clean_and_extract_info(text: str) -> Dict:
    """
    Clean text and extract structured information from CV content.
    
    Args:
        text (str): Raw text content from CV
        
    Returns:
        Dict: Structured candidate information
    """
    try:
        # Clean the text
        cleaned_text = clean_text(text)
        
        # Extract structured information
        candidate_info = {
            'name': extract_name(cleaned_text),
            'email': extract_email(cleaned_text),
            'phone': extract_phone(cleaned_text),
            'education': extract_education(cleaned_text),
            'experience': extract_experience(cleaned_text),
            'skills': extract_skills(cleaned_text)
        }
        
        logger.info(f"Successfully extracted information for candidate: {candidate_info['name']}")
        return candidate_info
        
    except Exception as e:
        logger.error(f"Error extracting information from text: {str(e)}")
        return {
            'name': 'Unknown',
            'email': '',
            'phone': '',
            'education': '',
            'experience': '',
            'skills': ''
        }

def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text (str): Raw text content
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s@.,()+-]', ' ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_name(text: str) -> str:
    """
    Extract candidate name from CV text.
    
    Args:
        text (str): CV text content
        
    Returns:
        str: Extracted name or 'Unknown'
    """
    try:
        lines = text.split('\n')
        
        # Look for name in first few lines
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            
            # Skip empty lines and common headers
            if not line or line.lower() in ['cv', 'resume', 'curriculum vitae']:
                continue
            
            # Check if line looks like a name (2-4 words, mostly alphabetic)
            words = line.split()
            if 2 <= len(words) <= 4:
                if all(word.replace('.', '').isalpha() or word.replace('.', '').replace('-', '').isalpha() 
                       for word in words):
                    return line
        
        # If no clear name found, try pattern matching
        name_patterns = [
            r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
            r'Name[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'^([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1)
        
        return 'Unknown'
        
    except Exception as e:
        logger.warning(f"Error extracting name: {str(e)}")
        return 'Unknown'

def extract_email(text: str) -> str:
    """
    Extract email address from CV text.
    
    Args:
        text (str): CV text content
        
    Returns:
        str: Extracted email or empty string
    """
    try:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group() if match else ''
    except Exception as e:
        logger.warning(f"Error extracting email: {str(e)}")
        return ''

def extract_phone(text: str) -> str:
    """
    Extract phone number from CV text.
    
    Args:
        text (str): CV text content
        
    Returns:
        str: Extracted phone number or empty string
    """
    try:
        # Various phone number patterns
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{10}',
            r'\+\d{1,3}\s?\d{8,12}'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return ''
    except Exception as e:
        logger.warning(f"Error extracting phone: {str(e)}")
        return ''

def extract_education(text: str) -> str:
    """
    Extract education information from CV text.
    
    Args:
        text (str): CV text content
        
    Returns:
        str: JSON string of education information
    """
    try:
        education_info = []
        
        # Look for education keywords
        education_keywords = [
            'education', 'qualification', 'degree', 'university', 'college',
            'bachelor', 'master', 'phd', 'diploma', 'certificate'
        ]
        
        lines = text.lower().split('\n')
        education_section = False
        
        for i, line in enumerate(lines):
            # Check if we're in education section
            if any(keyword in line for keyword in education_keywords):
                education_section = True
                continue
            
            # Stop if we hit another major section
            if education_section and any(word in line for word in ['experience', 'work', 'employment', 'skills']):
                break
            
            # Extract education entries
            if education_section and line.strip():
                # Look for degree patterns
                degree_patterns = [
                    r'(bachelor|master|phd|diploma|certificate).*?(?:in|of)?\s+([a-zA-Z\s]+)',
                    r'(b\.?[as]\.?|m\.?[as]\.?|ph\.?d\.?).*?([a-zA-Z\s]+)',
                ]
                
                for pattern in degree_patterns:
                    match = re.search(pattern, line)
                    if match:
                        education_info.append({
                            'degree': match.group(1),
                            'field': match.group(2).strip(),
                            'details': line.strip()
                        })
        
        return json.dumps(education_info) if education_info else ''
        
    except Exception as e:
        logger.warning(f"Error extracting education: {str(e)}")
        return ''

def extract_experience(text: str) -> str:
    """
    Extract work experience from CV text.
    
    Args:
        text (str): CV text content
        
    Returns:
        str: JSON string of experience information
    """
    try:
        experience_info = []
        
        # Look for experience keywords
        experience_keywords = [
            'experience', 'work', 'employment', 'career', 'professional',
            'position', 'role', 'job'
        ]
        
        lines = text.lower().split('\n')
        experience_section = False
        
        for i, line in enumerate(lines):
            # Check if we're in experience section
            if any(keyword in line for keyword in experience_keywords):
                experience_section = True
                continue
            
            # Stop if we hit another major section
            if experience_section and any(word in line for word in ['education', 'skills', 'qualification']):
                break
            
            # Extract experience entries
            if experience_section and line.strip():
                # Look for job title and company patterns
                job_patterns = [
                    r'([a-zA-Z\s]+?)\s+(?:at|@)\s+([a-zA-Z\s]+)',
                    r'([a-zA-Z\s]+?)\s*[-–]\s*([a-zA-Z\s]+)',
                ]
                
                for pattern in job_patterns:
                    match = re.search(pattern, line)
                    if match:
                        experience_info.append({
                            'title': match.group(1).strip(),
                            'company': match.group(2).strip(),
                            'details': line.strip()
                        })
        
        return json.dumps(experience_info) if experience_info else ''
        
    except Exception as e:
        logger.warning(f"Error extracting experience: {str(e)}")
        return ''

def extract_skills(text: str) -> str:
    """
    Extract skills from CV text.
    
    Args:
        text (str): CV text content
        
    Returns:
        str: JSON string of skills information
    """
    try:
        skills = []
        
        # Common technical skills patterns
        tech_skills_patterns = [
            r'\b(python|java|javascript|c\+\+|c#|php|ruby|go|rust|swift|kotlin)\b',
            r'\b(react|angular|vue|node\.?js|express|django|flask|spring)\b',
            r'\b(mysql|postgresql|mongodb|redis|elasticsearch)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins)\b',
            r'\b(git|github|gitlab|bitbucket)\b',
            r'\b(html|css|sass|less|bootstrap|tailwind)\b'
        ]
        
        text_lower = text.lower()
        
        # Extract technical skills
        for pattern in tech_skills_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.extend(matches)
        
        # Look for skills section
        lines = text.split('\n')
        skills_section = False
        
        for line in lines:
            line_lower = line.lower()
            
            # Check if we're in skills section
            if any(keyword in line_lower for keyword in ['skills', 'technologies', 'competencies']):
                skills_section = True
                continue
            
            # Stop if we hit another major section
            if skills_section and any(word in line_lower for word in ['experience', 'education', 'work']):
                break
            
            # Extract skills from skills section
            if skills_section and line.strip():
                # Split by common delimiters
                line_skills = re.split(r'[,;|•·]', line)
                for skill in line_skills:
                    skill = skill.strip()
                    if skill and len(skill) > 1:
                        skills.append(skill)
        
        # Remove duplicates and clean
        unique_skills = list(set([skill.strip().title() for skill in skills if skill.strip()]))
        
        return json.dumps(unique_skills) if unique_skills else ''
        
    except Exception as e:
        logger.warning(f"Error extracting skills: {str(e)}")
        return ''
