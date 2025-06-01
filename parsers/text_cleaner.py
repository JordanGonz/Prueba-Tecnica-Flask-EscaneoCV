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
        
        # Look for experience keywords (multilingual support)
        experience_keywords = [
            'experience', 'work', 'employment', 'career', 'professional',
            'position', 'role', 'job', 'experiencia', 'trabajo', 'empleo',
            'carrera', 'puesto', 'laboral', 'profesional', 'cargo'
        ]
        
        # Common job titles patterns
        job_title_patterns = [
            r'\b(director|manager|analista|desarrollador|programador|ingeniero|coordinador|especialista|consultor|supervisor|jefe|gerente|líder|lead|senior|junior)\b',
            r'\b(developer|analyst|engineer|coordinator|specialist|consultant|supervisor|chief|manager|leader)\b'
        ]
        
        # Company indicators
        company_indicators = [
            r'\b(company|empresa|corporation|corp|inc|ltd|llc|s\.a\.|s\.l\.|ltda)\b',
            r'\b(universidad|university|instituto|institute|hospital|clinic|bank|banco)\b'
        ]
        
        lines = text.split('\n')
        experience_section = False
        current_experience = {}
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            line_clean = line.strip()
            
            # Skip empty lines
            if not line_clean:
                continue
            
            # Check if we're entering experience section
            if any(keyword in line_lower for keyword in experience_keywords):
                experience_section = True
                continue
            
            # Stop if we hit education or skills section
            if experience_section and any(word in line_lower for word in ['education', 'educación', 'formación', 'skills', 'habilidades', 'competencias']):
                if current_experience:
                    experience_info.append(current_experience)
                break
            
            # If we're in experience section, try to extract information
            if experience_section and line_clean:
                # Check for job title patterns
                job_title_found = False
                for pattern in job_title_patterns:
                    if re.search(pattern, line_lower):
                        if current_experience:
                            experience_info.append(current_experience)
                        current_experience = {
                            'title': line_clean,
                            'company': '',
                            'details': line_clean
                        }
                        job_title_found = True
                        break
                
                # Check for company patterns
                if not job_title_found and any(re.search(pattern, line_lower) for pattern in company_indicators):
                    if current_experience:
                        current_experience['company'] = line_clean
                    else:
                        current_experience = {
                            'title': '',
                            'company': line_clean,
                            'details': line_clean
                        }
                
                # Check for date patterns (years of experience)
                date_patterns = [
                    r'\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b',
                    r'\b(19|20)\d{2}\s*[-–]\s*(present|actual|presente)\b',
                    r'\b\d{1,2}\s+(years?|años?)\b'
                ]
                
                if any(re.search(pattern, line_lower) for pattern in date_patterns):
                    if current_experience:
                        current_experience['details'] += f" | {line_clean}"
                    else:
                        current_experience = {
                            'title': '',
                            'company': '',
                            'details': line_clean
                        }
                
                # Look for "at" or "en" patterns for company
                at_patterns = [
                    r'(.+?)\s+(?:at|en|@)\s+(.+)',
                    r'(.+?)\s*[-–]\s*(.+)'
                ]
                
                for pattern in at_patterns:
                    match = re.search(pattern, line_clean)
                    if match and not job_title_found:
                        if current_experience:
                            experience_info.append(current_experience)
                        current_experience = {
                            'title': match.group(1).strip(),
                            'company': match.group(2).strip(),
                            'details': line_clean
                        }
                        break
        
        # Add the last experience if exists
        if current_experience and experience_section:
            experience_info.append(current_experience)
        
        # If no structured experience found but we found experience section, add as general text
        if not experience_info and experience_section:
            # Try to find any work-related content
            work_content = []
            for line in lines:
                line_clean = line.strip()
                if line_clean and any(keyword in line.lower() for keyword in ['work', 'job', 'company', 'position', 'role', 'empresa', 'trabajo', 'puesto']):
                    work_content.append(line_clean)
            
            if work_content:
                experience_info.append({
                    'title': 'Work Experience',
                    'company': '',
                    'details': ' | '.join(work_content[:3])  # Limit to first 3 relevant lines
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
