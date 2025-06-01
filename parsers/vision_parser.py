import os
import json
import base64
import logging
from io import BytesIO
from typing import Dict, List, Optional, Any, Union
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not found. Vision parsing will be disabled.")
    openai_client = None
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def pdf_to_images(pdf_path: str) -> List[Image.Image]:
    """
    Convert PDF to list of PIL Images.
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        List[Image.Image]: List of PIL images
    """
    try:
        images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=3)  # Max 3 pages
        logger.info(f"Converted PDF to {len(images)} images")
        return images
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        return []

def pdf_bytes_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """
    Convert PDF bytes to list of PIL Images.
    
    Args:
        pdf_bytes (bytes): PDF file as bytes
        
    Returns:
        List[Image.Image]: List of PIL images
    """
    try:
        images = convert_from_bytes(pdf_bytes, dpi=200, first_page=1, last_page=3)  # Max 3 pages
        logger.info(f"Converted PDF bytes to {len(images)} images")
        return images
    except Exception as e:
        logger.error(f"Error converting PDF bytes to images: {str(e)}")
        return []

def image_to_base64(image: Image.Image, format: str = "JPEG", max_size: tuple = (1024, 1024)) -> str:
    """
    Convert PIL Image to base64 string.
    
    Args:
        image (Image.Image): PIL Image
        format (str): Image format (JPEG, PNG)
        max_size (tuple): Maximum size for resizing
        
    Returns:
        str: Base64 encoded image
    """
    try:
        # Resize image if too large
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB' and format == 'JPEG':
            image = image.convert('RGB')
        
        buffer = BytesIO()
        image.save(buffer, format=format, quality=85, optimize=True)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return ""

def analyze_cv_with_vision(images: List[Image.Image]) -> Dict:
    """
    Analyze CV images using OpenAI Vision API.
    
    Args:
        images (List[Image.Image]): List of CV page images
        
    Returns:
        Dict: Extracted candidate information
    """
    if not openai_client:
        logger.warning("OpenAI client not available. Skipping vision analysis.")
        return {}
    
    try:
        # Convert images to base64
        image_messages = []
        for i, image in enumerate(images[:2]):  # Analyze max 2 pages
            base64_image = image_to_base64(image)
            if base64_image:
                image_messages.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
        
        if not image_messages:
            logger.warning("No valid images to analyze")
            return {}
        
        # Prepare the prompt for CV analysis
        prompt = """
        Analyze this CV/resume image and extract the following information in JSON format:
        
        {
            "name": "Full name of the candidate",
            "email": "Email address",
            "phone": "Phone number",
            "skills": ["list", "of", "technical", "skills"],
            "experience": [
                {
                    "title": "Job title",
                    "company": "Company name",
                    "duration": "Duration or dates",
                    "description": "Brief description of role"
                }
            ],
            "education": [
                {
                    "degree": "Degree name",
                    "institution": "University/School name",
                    "year": "Graduation year or duration",
                    "field": "Field of study"
                }
            ],
            "languages": ["list", "of", "languages"],
            "certifications": ["list", "of", "certifications"],
            "summary": "Brief professional summary"
        }
        
        Extract as much information as possible. If a field is not available, use an empty string or empty array.
        Pay special attention to work experience, including job titles, companies, and durations.
        For skills, include both technical and soft skills mentioned.
        Ensure the JSON is valid and properly formatted.
        """
        
        # Create message with text and images
        content = [{"type": "text", "text": prompt}] + image_messages
        messages = [{"role": "user", "content": content}]
        
        # Call OpenAI Vision API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Latest OpenAI model with vision capabilities
            messages=messages,  # type: ignore
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            logger.info("Successfully analyzed CV with OpenAI Vision")
        else:
            result = {}
            logger.warning("Empty response from OpenAI Vision")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing CV with vision: {str(e)}")
        return {}

def extract_cv_data_with_vision(file_path: str, file_type: str) -> Dict:
    """
    Extract CV data using vision analysis.
    
    Args:
        file_path (str): Path to CV file
        file_type (str): Type of file (pdf, docx, jpg, png)
        
    Returns:
        Dict: Extracted candidate information
    """
    try:
        images = []
        
        if file_type.lower() == 'pdf':
            images = pdf_to_images(file_path)
        elif file_type.lower() in ['jpg', 'jpeg', 'png']:
            # If it's already an image
            image = Image.open(file_path)
            images = [image]
        elif file_type.lower() == 'docx':
            # For DOCX, we'll skip vision analysis for now
            logger.info("DOCX vision analysis not implemented yet")
            return {}
        
        if not images:
            logger.warning(f"No images generated from {file_type} file")
            return {}
        
        # Analyze with OpenAI Vision
        result = analyze_cv_with_vision(images)
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting CV data with vision: {str(e)}")
        return {}

def generate_text_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using OpenAI.
    
    Args:
        text (str): Text to embed
        
    Returns:
        List[float]: Embedding vector
    """
    if not openai_client:
        logger.warning("OpenAI client not available. Skipping embedding generation.")
        return []
    
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            encoding_format="float"
        )
        
        embedding = response.data[0].embedding
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return []

def search_candidates_semantic(query: str, candidate_embeddings: List[Dict], top_k: int = 10) -> List[Dict]:
    """
    Perform semantic search using embeddings.
    
    Args:
        query (str): Search query
        candidate_embeddings (List[Dict]): List of candidates with embeddings
        top_k (int): Number of top results to return
        
    Returns:
        List[Dict]: Ranked search results
    """
    if not openai_client:
        logger.warning("OpenAI client not available. Skipping semantic search.")
        return []
    
    try:
        # Generate embedding for query
        query_embedding = generate_text_embedding(query)
        if not query_embedding:
            return []
        
        # Calculate similarity scores
        results = []
        for candidate in candidate_embeddings:
            if 'embedding' not in candidate or not candidate['embedding']:
                continue
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, candidate['embedding'])
            results.append({
                'candidate': candidate,
                'similarity': similarity
            })
        
        # Sort by similarity and return top k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return [r['candidate'] for r in results[:top_k]]
        
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        return []

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1 (List[float]): First vector
        vec2 (List[float]): Second vector
        
    Returns:
        float: Cosine similarity score
    """
    try:
        import numpy as np
        
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {str(e)}")
        return 0.0