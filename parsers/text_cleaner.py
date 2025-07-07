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
    Clean and normalize text content, reintroduce section-based newlines.

    Args:
        text (str): Raw text content

    Returns:
        str: Cleaned and structured text
    """
    if not text:
        return ""

    # Forzar saltos de línea antes de encabezados comunes de CV
    section_keywords = [
        r"(información personal|educación|educacion|formación|experience|experiencia|work experience|habilidades|skills|competencias|certificaciones?|summary|resumen|idiomas|languages)"
    ]
    for pattern in section_keywords:
        text = re.sub(pattern, r'\n\1', text, flags=re.IGNORECASE)

    # Forzar salto de línea antes de frases clave
    line_split_clues = [
        r"(universidad[\w\s]*:?)",
        r"(colegio[\w\s]*:?)",
        r"(unidad educativa[\w\s]*:?)",
        r"(título[\w\s]*:?)",
        r"(licenciatura[\w\s]*:?)",
        r"(ingeniero[\w\s]*:?)",
        r"(egresado[\w\s]*\.?)",
        r"(estudiante[\w\s]*\.?)"
    ]
    for pattern in line_split_clues:
        text = re.sub(pattern, r'\n\1', text, flags=re.IGNORECASE)

    # Limpiar caracteres especiales pero mantener puntuaciones útiles
    text = re.sub(r'[^\w\s@.,:+()\-]', ' ', text)

    # Reconvertir múltiples espacios
    text = re.sub(r'\s+', ' ', text)

    # Restaurar saltos de línea donde correspondan
    text = re.sub(r'(?<=[a-zA-Z0-9])\n(?=[a-zA-Z])', r'\n', text)

    # Añadir salto real tras puntos seguidos de mayúsculas
    text = re.sub(r'\.\s+(?=[A-ZÁÉÍÓÚÑ])', '.\n', text)

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
    Returns:
        str: JSON string of education information
    """
    try:
        education_info = []

        raw_lines = text.split('\n')
        lines = [line.strip() for line in raw_lines if line.strip()]
        lines_lower = [line.lower() for line in lines]

        # Detectar si hay línea explícita con "Universidad: ..."
        explicit_institution = ""
        for line in lines:
            if re.match(r'^universidad\s*:', line.lower()):
                explicit_institution = line.split(':', 1)[1].strip()
                break

        # Palabras clave para identificar instituciones educativas
        education_keywords = ['universidad', 'instituto', 'colegio', 'unidad educativa', 'escuela', 'school', 'college']
        degree_keywords = ['ingeniero', 'licenciatura', 'bachiller', 'doctorado', 'técnico', 'magister', 'título']
        date_pattern = re.compile(r'\b(desde\s*)?(19|20)\d{2}\s*[-–]\s*(hasta\s*)?(19|20)\d{2}\b', re.IGNORECASE)

        i = 0
        while i < len(lines):
            line = lines[i]
            line_lower = lines_lower[i]

            # Si contiene fecha o palabras clave, es un bloque de educación
            if date_pattern.search(line) or any(k in line_lower for k in education_keywords + degree_keywords):
                block = [line]

                # Tomar hasta 2 líneas siguientes si parecen ser continuación
                for j in range(1, 3):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if next_line and not re.match(r'^[A-Z\s]{3,}$', next_line):  # evita secciones
                            block.append(next_line)

                full_text = ' '.join(block)

                # Extraer institución
                institution = ""
                for kw in education_keywords:
                    matches = re.findall(rf'({kw}[^\n]*)', full_text, re.IGNORECASE)
                    if matches:
                        institution = max(matches, key=len).strip()
                        break

                # Si no se encontró en el bloque, usar la explícita
                if not institution and explicit_institution:
                    institution = explicit_institution

                # Extraer grado y campo
                degree_match = re.search(
                    r'(ingeniero|licenciatura|bachiller|técnico|tecnólogo|doctorado|magister)\s*(en|de)?\s*([a-zA-ZÁÉÍÓÚñÑ\s\-]+)?',
                    full_text, re.IGNORECASE
                )
                degree = field = ""
                if degree_match:
                    degree = degree_match.group(1).strip().title()
                    field = degree_match.group(3).strip().title() if degree_match.group(3) else ""

                # Estado (opcional)
                status = ""
                if "egresado" in full_text.lower():
                    status = "Egresado"
                elif "estudiante" in full_text.lower():
                    status = "Estudiante"

                if institution or degree or field:
                    education_info.append({
                        'degree': degree or '',
                        'field': field or '',
                        'institution': institution or '',
                        'status': status or '',
                        'details': full_text.strip()
                    })


                i += len(block)
            i += 1

        return json.dumps(education_info, ensure_ascii=False) if education_info else ''
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
            if any(keyword in line_lower for keyword in experience_keywords + ['cargo']):
                experience_section = True
                continue
            
            # Stop if we hit education or skills section
            if experience_section and any(word in line_lower for word in ['education', 'educación', 'formación', 'skills', 'habilidades', 'competencias', 'idiomas']):
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
    Extract skills from CV text (técnicas y blandas).

    Args:
        text (str): CV text content

    Returns:
        str: JSON string of skills information
    """
    try:
        skills = []

        # Preprocesamiento básico
        text_lower = text.lower()
        lines = text.split('\n')

        # 1. Extraer patrones técnicos frecuentes
        tech_skills_patterns = [
            r'\b(python|java|javascript|typescript|c\+\+|c#|php|ruby|go|rust|swift|kotlin)\b',
            r'\b(react|angular|vue|node\.?js|express|django|flask|springboot?)\b',
            r'\b(mysql|postgresql|sql server|mongodb|oracle 11g?|redis|elasticsearch)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|github actions?)\b',
            r'\b(git|github|gitlab|bitbucket)\b',
            r'\b(html|css|sass|less|bootstrap|tailwindcss?)\b',
            r'\b(powerbi|tableau|jira|postman|soapui|databricks|netbeans|android studio)\b',
            r'\b(etl|jwt|mvc|iis|gnu/linux|sencha js|laravel|\.net\s*6?|c\.net|mantenimiento técnico|microsoft office)\b'
        ]

        for pattern in tech_skills_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.extend(matches)

        # 2. Extraer frases tipo: "uso de", "manejo de"
        phrase_based_patterns = [
            r'(?:uso de|manejo de|experiencia en|conocimiento en)\s+([a-zA-Z\s\.\-]{2,60})'
        ]
        for pattern in phrase_based_patterns:
            matches = re.findall(pattern, text_lower)
            for phrase in matches:
                parts = re.split(r'\s+y\s+|,|;|•|·', phrase)
                skills.extend([p.strip() for p in parts if p.strip()])

        # 3. Buscar sección de habilidades explícita
        section_headers = ['conocimientos técnicos', 'habilidades', 'skills', 'competencias']
        collecting = False

        for line in lines:
            line_lower = line.lower().strip()

            # Detectar encabezado
            if any(header in line_lower for header in section_headers):
                collecting = True
                continue

            # Detener si aparece otra sección
            if collecting and any(stop in line_lower for stop in ['experiencia', 'proyecto', 'educación', 'formación', 'referencias']):
                break

            # Procesar líneas de habilidades en columnas
            if collecting and line.strip():
                # Separar por espacios amplios, tabs o bullets
                items = re.split(r'\s{2,}|\t|[,;•·]', line)
                for item in items:
                    skill = item.strip()
                    if skill and len(skill) > 1:
                        skills.append(skill)

        # 4. Limpiar y unificar
        unique_skills = sorted(set(
            s.strip().title()
            for s in skills
            if s and len(s.strip()) >= 2
        ))

        return json.dumps(unique_skills, ensure_ascii=False) if unique_skills else ''

    except Exception as e:
        logger.warning(f"Error extracting skills: {str(e)}")
        return ''
