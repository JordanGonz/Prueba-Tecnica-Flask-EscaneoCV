import logging
from typing import List, Optional
from sqlalchemy import or_, and_
from app import db
from models import Candidate

logger = logging.getLogger(__name__)

def search_candidates(query: str) -> List[Candidate]:
    """
    Search for candidates based on text query.
    Performs text-based search across multiple fields.
    
    Args:
        query (str): Search query string
        
    Returns:
        List[Candidate]: List of matching candidates
    """
    try:
        if not query or not query.strip():
            return []
        
        search_term = f"%{query.strip()}%"
        
        # Search across multiple fields
        candidates = db.session.query(Candidate).filter(
            or_(
                Candidate.name.ilike(search_term),
                Candidate.email.ilike(search_term),
                Candidate.phone.ilike(search_term),
                Candidate.skills.ilike(search_term),
                Candidate.experience.ilike(search_term),
                Candidate.education.ilike(search_term),
                Candidate.full_text.ilike(search_term)
            )
        ).order_by(Candidate.created_at.desc()).limit(50).all()
        
        logger.info(f"Search for '{query}' returned {len(candidates)} candidates")
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
