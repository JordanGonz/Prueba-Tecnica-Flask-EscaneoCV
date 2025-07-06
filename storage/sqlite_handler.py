import logging
from typing import List, Optional
from sqlalchemy import or_, and_
from extensions import db
from models import Candidate
import re
import json
from constants.constants import UNIVERSITY_ALIASES,ROLE_ALIASES

logger = logging.getLogger(__name__)

def extract_keywords(text: str) -> List[str]:
    common_words = {'dame', 'los', 'las', 'en', 'con', 'de', 'que', 'quiero', 'y', 'para', 'un', 'una', 'me'}
    words = re.findall(r'\b\w+\b', text.lower())
    expanded_words = []

    for w in words:
        if w not in common_words and len(w) > 2:
            if w in UNIVERSITY_ALIASES:
                expanded_words.append(UNIVERSITY_ALIASES[w].lower())
            elif w in ROLE_ALIASES:
                expanded_words.extend(ROLE_ALIASES[w])
            else:
                expanded_words.append(w)

    return expanded_words


def is_university(institution: str) -> bool:
    """
    Determina si una institución es una universidad o equivalente.
    """
    institution = institution.lower()
    universidad_keywords = ["universidad", "escuela superior", "politécnica", "polytechnic", "institute of technology"]
    return any(kw in institution for kw in universidad_keywords)


def search_candidates(query: str) -> List[Candidate]:
    try:
        if not query or not query.strip():
            return []

        keywords = extract_keywords(query)

        # Genera condiciones por campo (con OR interno por keyword)
        education_filter = or_(*[Candidate.education.ilike(f"%{kw}%") for kw in keywords])
        skills_filter = or_(*[Candidate.skills.ilike(f"%{kw}%") for kw in keywords])
        fulltext_filter = or_(*[Candidate.full_text.ilike(f"%{kw}%") for kw in keywords])
        experience_filter = or_(*[Candidate.experience.ilike(f"%{kw}%") for kw in keywords])

        candidates = db.session.query(Candidate).filter(
            or_(
                education_filter,
                skills_filter,
                fulltext_filter,
                experience_filter
            )
        ).order_by(Candidate.created_at.desc()).limit(50).all()

        # Si se menciona "universidad", filtrar los que tienen universidades reales
        if any(word in query.lower() for word in ["universidad", "universidades"]):
            filtered_candidates = []
            for c in candidates:
                try:
                    education_data = json.loads(c.education) if isinstance(c.education, str) else c.education
                    if any(is_university(ed.get("institution", "")) for ed in education_data if isinstance(ed, dict)):
                        filtered_candidates.append(c)
                except Exception as parse_error:
                    logger.warning(f"Error parsing education JSON for candidate {c.id}: {parse_error}")
            candidates = filtered_candidates

        logger.info(f"Search for keywords {keywords} returned {len(candidates)} candidates")
        return candidates

    except Exception as e:
        logger.error(f"Error searching candidates: {str(e)}")
        raise Exception(f"Database search failed: {str(e)}")


def get_all_candidates(limit: int = 100, offset: int = 0) -> List[Candidate]:
    """
    Retrieve all candidates with pagination.
    
    Args:
        limit (int): Maximum number of candidates to return
        offset (int): Number of candidates to skip
        
    Returns:
        List[Candidate]: List of candidates
    """
    try:
        candidates = db.session.query(Candidate)\
            .order_by(Candidate.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        logger.info(f"Retrieved {len(candidates)} candidates (limit: {limit}, offset: {offset})")
        return candidates
        
    except Exception as e:
        logger.error(f"Error retrieving candidates: {str(e)}")
        raise Exception(f"Database query failed: {str(e)}")

def get_candidate_by_id(candidate_id: int) -> Optional[Candidate]:
    """
    Retrieve a specific candidate by ID.
    
    Args:
        candidate_id (int): Candidate ID
        
    Returns:
        Optional[Candidate]: Candidate object or None if not found
    """
    try:
        candidate = db.session.get(Candidate, candidate_id)
        
        if candidate:
            logger.info(f"Retrieved candidate: {candidate.name} (ID: {candidate_id})")
        else:
            logger.warning(f"Candidate not found with ID: {candidate_id}")
        
        return candidate
        
    except Exception as e:
        logger.error(f"Error retrieving candidate {candidate_id}: {str(e)}")
        raise Exception(f"Database query failed: {str(e)}")

def get_candidates_by_skill(skill: str) -> List[Candidate]:
    """
    Search for candidates by specific skill.
    
    Args:
        skill (str): Skill to search for
        
    Returns:
        List[Candidate]: List of candidates with the skill
    """
    try:
        skill_term = f"%{skill.strip()}%"
        
        candidates = db.session.query(Candidate).filter(
            or_(
                Candidate.skills.ilike(skill_term),
                Candidate.full_text.ilike(skill_term)
            )
        ).order_by(Candidate.created_at.desc()).all()
        
        logger.info(f"Skill search for '{skill}' returned {len(candidates)} candidates")
        return candidates
        
    except Exception as e:
        logger.error(f"Error searching candidates by skill: {str(e)}")
        raise Exception(f"Skill search failed: {str(e)}")

def get_candidates_count() -> int:
    """
    Get total number of candidates in the database.
    
    Returns:
        int: Total number of candidates
    """
    try:
        count = db.session.query(Candidate).count()
        logger.info(f"Total candidates count: {count}")
        return count
        
    except Exception as e:
        logger.error(f"Error counting candidates: {str(e)}")
        raise Exception(f"Database count failed: {str(e)}")

def delete_candidate(candidate_id: int) -> bool:
    """
    Delete a candidate from the database.
    
    Args:
        candidate_id (int): Candidate ID to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        candidate = db.session.get(Candidate, candidate_id)
        
        if not candidate:
            logger.warning(f"Candidate not found for deletion: {candidate_id}")
            return False
        
        db.session.delete(candidate)
        db.session.commit()
        
        logger.info(f"Successfully deleted candidate: {candidate.name} (ID: {candidate_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting candidate {candidate_id}: {str(e)}")
        db.session.rollback()
        raise Exception(f"Database deletion failed: {str(e)}")
