"""
Vector database search functionality using pgvector.
Provides high-performance semantic search with native PostgreSQL vector operations.
"""
import json
import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text
from app import db
from models import Candidate

logger = logging.getLogger(__name__)

def store_embedding_vector(candidate_id: int, embedding: List[float]) -> bool:
    """
    Store embedding as native vector type in PostgreSQL.
    
    Args:
        candidate_id: ID of the candidate
        embedding: List of float values representing the embedding
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert embedding to PostgreSQL vector format
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        query = text("""
            UPDATE candidate 
            SET embedding_vector = :embedding::vector(1536),
                text_embedding = :embedding_json
            WHERE id = :candidate_id
        """)
        
        db.session.execute(query, {
            'embedding': embedding_str,
            'embedding_json': json.dumps(embedding),
            'candidate_id': candidate_id
        })
        db.session.commit()
        
        logger.info(f"Successfully stored vector embedding for candidate {candidate_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing embedding for candidate {candidate_id}: {e}")
        db.session.rollback()
        return False

def vector_similarity_search(query_embedding: List[float], limit: int = 10, min_similarity: float = 0.1) -> List[Dict]:
    """
    Perform high-performance vector similarity search using pgvector.
    
    Args:
        query_embedding: Query embedding vector
        limit: Maximum number of results to return
        min_similarity: Minimum cosine similarity threshold
        
    Returns:
        List of candidate dictionaries with similarity scores
    """
    try:
        # Convert query embedding to PostgreSQL vector format
        query_vector = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Use pgvector's native cosine similarity with HNSW index
        query = text("""
            SELECT 
                c.id,
                c.name,
                c.email,
                c.phone,
                c.skills,
                c.experience,
                c.education,
                c.summary,
                c.original_filename,
                c.created_at,
                1 - (c.embedding_vector <=> :query_vector::vector(1536)) as similarity
            FROM candidate c
            WHERE c.embedding_vector IS NOT NULL
            ORDER BY c.embedding_vector <=> :query_vector::vector(1536)
            LIMIT :limit
        """)
        
        result = db.session.execute(query, {
            'query_vector': query_vector,
            'limit': limit
        })
        
        candidates = []
        for row in result:
            similarity = float(row.similarity)
            
            # Filter by minimum similarity threshold
            if similarity >= min_similarity:
                candidates.append({
                    'id': row.id,
                    'name': row.name,
                    'email': row.email or '',
                    'phone': row.phone or '',
                    'skills': row.skills or '',
                    'experience': row.experience or '',
                    'education': row.education or '',
                    'summary': row.summary or '',
                    'filename': row.original_filename,
                    'created_at': row.created_at.isoformat() if row.created_at else '',
                    'similarity': similarity
                })
        
        logger.info(f"Vector search returned {len(candidates)} results with similarity >= {min_similarity}")
        return candidates
        
    except Exception as e:
        logger.error(f"Error in vector similarity search: {e}")
        return []

def get_candidates_with_vectors(limit: int = 100) -> List[Dict]:
    """
    Get all candidates with their vector embeddings for visualization.
    
    Args:
        limit: Maximum number of candidates to return
        
    Returns:
        List of candidates with embeddings
    """
    try:
        query = text("""
            SELECT 
                c.id,
                c.name,
                c.email,
                c.phone,
                c.skills,
                c.text_embedding,
                c.embedding_vector
            FROM candidate c
            WHERE c.embedding_vector IS NOT NULL
            ORDER BY c.created_at DESC
            LIMIT :limit
        """)
        
        result = db.session.execute(query, {'limit': limit})
        
        candidates = []
        for row in result:
            # Parse embedding from JSON for visualization
            embedding = []
            if row.text_embedding:
                try:
                    embedding = json.loads(row.text_embedding)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON embedding for candidate {row.id}")
            
            candidates.append({
                'id': row.id,
                'name': row.name,
                'email': row.email or '',
                'phone': row.phone or '',
                'skills': row.skills or '',
                'embedding': embedding
            })
        
        logger.info(f"Retrieved {len(candidates)} candidates with vectors")
        return candidates
        
    except Exception as e:
        logger.error(f"Error retrieving candidates with vectors: {e}")
        return []

def get_vector_statistics() -> Dict:
    """
    Get statistics about the vector database.
    
    Returns:
        Dictionary with vector database statistics
    """
    try:
        stats_query = text("""
            SELECT 
                COUNT(*) as total_candidates,
                COUNT(embedding_vector) as candidates_with_vectors,
                AVG(array_length(string_to_array(embedding_vector::text, ','), 1)) as avg_dimensions
            FROM candidate
        """)
        
        result = db.session.execute(stats_query).fetchone()
        
        return {
            'total_candidates': result.total_candidates,
            'candidates_with_vectors': result.candidates_with_vectors,
            'avg_dimensions': int(result.avg_dimensions) if result.avg_dimensions else 0,
            'vector_coverage': (result.candidates_with_vectors / result.total_candidates * 100) if result.total_candidates > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting vector statistics: {e}")
        return {
            'total_candidates': 0,
            'candidates_with_vectors': 0,
            'avg_dimensions': 0,
            'vector_coverage': 0
        }

def find_similar_candidates(candidate_id: int, limit: int = 5) -> List[Dict]:
    """
    Find candidates similar to a given candidate using vector similarity.
    
    Args:
        candidate_id: ID of the reference candidate
        limit: Number of similar candidates to return
        
    Returns:
        List of similar candidates with similarity scores
    """
    try:
        # Get the reference candidate's embedding
        ref_query = text("""
            SELECT embedding_vector FROM candidate 
            WHERE id = :candidate_id AND embedding_vector IS NOT NULL
        """)
        
        ref_result = db.session.execute(ref_query, {'candidate_id': candidate_id}).fetchone()
        
        if not ref_result:
            logger.warning(f"No embedding found for candidate {candidate_id}")
            return []
        
        # Find similar candidates
        similar_query = text("""
            SELECT 
                c.id,
                c.name,
                c.email,
                c.skills,
                1 - (c.embedding_vector <=> :ref_vector) as similarity
            FROM candidate c
            WHERE c.embedding_vector IS NOT NULL 
            AND c.id != :candidate_id
            ORDER BY c.embedding_vector <=> :ref_vector
            LIMIT :limit
        """)
        
        result = db.session.execute(similar_query, {
            'ref_vector': ref_result.embedding_vector,
            'candidate_id': candidate_id,
            'limit': limit
        })
        
        similar_candidates = []
        for row in result:
            similar_candidates.append({
                'id': row.id,
                'name': row.name,
                'email': row.email or '',
                'skills': row.skills or '',
                'similarity': float(row.similarity)
            })
        
        logger.info(f"Found {len(similar_candidates)} similar candidates for candidate {candidate_id}")
        return similar_candidates
        
    except Exception as e:
        logger.error(f"Error finding similar candidates: {e}")
        return []