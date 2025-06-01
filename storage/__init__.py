"""
Storage module for handling database operations and candidate data management.
"""

from .sqlite_handler import search_candidates, get_all_candidates, get_candidate_by_id

__all__ = ['search_candidates', 'get_all_candidates', 'get_candidate_by_id']
